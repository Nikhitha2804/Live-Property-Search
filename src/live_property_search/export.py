from __future__ import annotations

import sys
import io
import json
import logging
import pandas as pd
import psycopg2
import psycopg2.extras
from pathlib import Path
from datetime import datetime

# Add src directory to path for direct script execution
if __name__ == '__main__':
    src_path = Path(__file__).resolve().parents[1]
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


from live_property_search.db import get_db_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Exporter:
    def __init__(self):
        self.export_report = {
            'start_time': None,
            'end_time': None,
            'rows_exported': 0,
            'table_name': None,
            'export_method': None,
            'duration_seconds': None
        }

    @staticmethod
    def _sql_type_for_series(s: pd.Series) -> str:
        if pd.api.types.is_integer_dtype(s.dtype):
            return "INTEGER"
        if pd.api.types.is_float_dtype(s.dtype):
            return "DOUBLE PRECISION"
        if pd.api.types.is_bool_dtype(s.dtype):
            return "BOOLEAN"
        if pd.api.types.is_datetime64_any_dtype(s.dtype):
            return "DATE"
        return "TEXT"

    def create_table(self, conn: psycopg2.extensions.connection, df: pd.DataFrame, table_name: str, replace: bool = True) -> None:
        logger.info(f"Creating table '{table_name}' with {len(df.columns)} columns...")
        cols = []
        for col in df.columns:
            sqltype = self._sql_type_for_series(df[col])
            cols.append(f'"{col}" {sqltype}')
            logger.debug(f"Column '{col}' -> {sqltype}")

        pk_clause = ''
        if 'property_id' in df.columns:
            pk_clause = ', PRIMARY KEY ("property_id")'
            logger.info("Setting property_id as primary key")

        with conn.cursor() as cur:
            if replace:
                logger.info(f"Dropping existing table '{table_name}' if exists")
                cur.execute(f'DROP TABLE IF EXISTS "{table_name}"')
            create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(cols)}{pk_clause})'
            cur.execute(create_sql)
        conn.commit()
        logger.info(f"Table '{table_name}' created successfully")

    def export(self, df: pd.DataFrame, table_name: str, if_exists: str = 'replace') -> None:
        self.export_report['start_time'] = datetime.now().isoformat()
        self.export_report['table_name'] = table_name
        logger.info(f"Starting export to table '{table_name}' with if_exists='{if_exists}'")
        logger.info(f"DataFrame has {len(df)} rows and {len(df.columns)} columns")
        
        if if_exists not in ('replace', 'append', 'fail'):
            raise ValueError("if_exists must be one of 'replace', 'append', or 'fail'")

        conn = get_db_connection()
        if conn is None:
            raise RuntimeError('Database connection failed; ensure DATABASE_URL is set')
        
        logger.info("Database connection established")

        try:
            if if_exists == 'replace':
                self.create_table(conn, df, table_name, replace=True)
            elif if_exists == 'append':
                self.create_table(conn, df, table_name, replace=False)
            else:
                with conn.cursor() as cur:
                    cur.execute("SELECT to_regclass(%s)", (table_name,))
                    exists = cur.fetchone()[0]
                    if exists:
                        raise RuntimeError(f"Table {table_name} already exists")

            # Check if dataframe is empty
            if df.empty:
                logger.warning("DataFrame is empty, skipping export")
                return

            columns = list(df.columns)
            cols_sql = ','.join([f'"{c}"' for c in columns])
            logger.info(f"Columns to export: {cols_sql}")

            # Load data using execute_values (more reliable than COPY for some network configs)
            logger.info(f"Loading {len(df)} rows into PostgreSQL using execute_values...")
            logger.info("This may take several minutes for large datasets...")
            
            # Set session performance parameters
            with conn.cursor() as cur:
                cur.execute("SET work_mem = '512MB'")
                cur.execute("SET synchronous_commit = 'off'")
            
            # Convert DataFrame to list of tuples for execute_values
            data = [tuple(row) for row in df[columns].values]
            
            # Use execute_values with batching and retry logic
            batch_size = 5000  # Reduced batch size to prevent timeouts
            total_batches = (len(data) + batch_size - 1) // batch_size
            max_retries = 3
            
            for i in range(total_batches):
                start_idx = i * batch_size
                end_idx = min((i + 1) * batch_size, len(data))
                batch_data = data[start_idx:end_idx]
                
                logger.info(f"Processing batch {i+1}/{total_batches} (rows {start_idx}-{end_idx})...")
                
                # Retry logic for connection failures
                for attempt in range(max_retries):
                    try:
                        with conn.cursor() as cur:
                            insert_sql = f'INSERT INTO "{table_name}" ({cols_sql}) VALUES %s'
                            psycopg2.extras.execute_values(cur, insert_sql, batch_data, page_size=batch_size)
                        conn.commit()
                        logger.info(f"Batch {i+1}/{total_batches} completed")
                        break
                    except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                        logger.warning(f"Connection error on batch {i+1}, attempt {attempt+1}/{max_retries}: {e}")
                        if attempt < max_retries - 1:
                            conn.close()
                            conn = get_db_connection()
                            if conn is None:
                                raise RuntimeError('Failed to reconnect to database')
                            logger.info("Reconnected to database")
                        else:
                            raise
            
            self.export_report['rows_exported'] = len(df)
            self.export_report['export_method'] = 'execute_values with batching'
            self.export_report['end_time'] = datetime.now().isoformat()
            
            start_dt = datetime.fromisoformat(self.export_report['start_time'])
            end_dt = datetime.fromisoformat(self.export_report['end_time'])
            self.export_report['duration_seconds'] = (end_dt - start_dt).total_seconds()
            
            logger.info(f"PostgreSQL load completed successfully. Exported {len(df)} rows in {self.export_report['duration_seconds']:.2f} seconds")
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            raise
        finally:
            conn.close()
            logger.info("Database connection closed")


def generate_and_save_report(raw_df: pd.DataFrame, cleaned_df: pd.DataFrame, export_report: dict = None) -> dict:
    logger.info("Generating data quality report...")
    rules_applied = [
        "Trimmed and normalized text fields.",
        "Preserved postcode and property_id as string-safe identifiers.",
        "Dropped all-null or low-analytical-value feed columns.",
        "Removed duplicate property IDs.",
        "Parsed RunDate to ISO date.",
        "Nullified impossible numeric values before imputation.",
        "Filled missing coordinates using postcode, city/state, then state medians.",
        "Filled land-listing bedrooms, bathrooms, and living space with 0 where appropriate.",
        "Filled remaining numeric gaps with property-type/state medians, then broader medians.",
        "Converted land measurements to land_space_sqft before imputing comparable land size.",
        "Dropped rows still missing production-critical identifiers, location, price, or coordinates."
    ]
    
    columns_removed = [
        "apartment",
        "broker_id",
        "year_build",
        "total_num_units",
        "listing_age",
        "agent_name",
        "agent_phone"
    ]

    before_stats = {
        "rows": len(raw_df),
        "columns": len(raw_df.columns),
        "duplicate_property_id_count": int(raw_df['property_id'].duplicated().sum()) if 'property_id' in raw_df.columns else 0,
        "null_counts": raw_df.isnull().sum().to_dict(),
        "property_type_counts": raw_df['property_type'].value_counts().to_dict() if 'property_type' in raw_df.columns else {},
        "state_counts": raw_df['state'].value_counts().to_dict() if 'state' in raw_df.columns else {}
    }
    logger.info(f"Before cleaning: {before_stats['rows']} rows, {before_stats['columns']} columns")
    
    after_stats = {
        "rows": len(cleaned_df),
        "columns": len(cleaned_df.columns),
        "duplicate_property_id_count": int(cleaned_df['property_id'].duplicated().sum()) if 'property_id' in cleaned_df.columns else 0,
        "null_counts": cleaned_df.isnull().sum().to_dict(),
        "property_type_counts": cleaned_df['property_type'].value_counts().to_dict() if 'property_type' in cleaned_df.columns else {},
        "state_counts": cleaned_df['state'].value_counts().to_dict() if 'state' in cleaned_df.columns else {}
    }
    logger.info(f"After cleaning: {after_stats['rows']} rows, {after_stats['columns']} columns")

    report = {
        "source_file": "data\\600K US Housing Properties.csv",
        "cleaned_file": "data\\cleaned_data.csv",
        "random_sample_file": "data\\random_records_sample.csv",
        "rules_applied": rules_applied,
        "before": before_stats,
        "after": after_stats,
        "rows_removed": len(raw_df) - len(cleaned_df),
        "columns_removed": columns_removed
    }
    
    if export_report:
        report['export'] = export_report
        logger.info(f"Export report included: {export_report['rows_exported']} rows exported in {export_report['duration_seconds']:.2f} seconds")

    # Save report
    data_dir = Path(__file__).resolve().parents[2] / 'data'
    report_path = data_dir / 'data_quality_report.json'
    with open(report_path, 'w', encoding='utf-8') as rf:
        json.dump(report, rf, indent=2)
    
    logger.info(f"Data quality report saved to: {report_path}")

    return report


def main():
    logger.info("=" * 60)
    logger.info("Starting PostgreSQL export")
    logger.info("=" * 60)

    data_dir = Path(__file__).resolve().parents[2] / "data"

    # Read cleaned dataset directly
    cleaned_csv = data_dir / "cleaned_data.csv"

    logger.info(f"Reading cleaned dataset: {cleaned_csv}")

    df = pd.read_csv(cleaned_csv, low_memory=False)

    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")

    # Export to PostgreSQL
    exporter = Exporter()

    logger.info('Exporting cleaned data to table "housedata"...')

    exporter.export(
        df,
        table_name="housedata",
        if_exists="replace"
    )

    logger.info("=" * 60)
    logger.info("Export completed successfully")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
