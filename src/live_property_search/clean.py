from __future__ import annotations

import pandas as pd
import numpy as np
import re
import logging
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CleanDataset:
    def __init__(self, raw_csv: Optional[str] = None):
        default_path = Path(__file__).resolve().parents[2] / 'data' / '600K US Housing Properties.csv'
        self.raw_csv = raw_csv or str(default_path)
        self.df: Optional[pd.DataFrame] = None
        self.cleaning_report = {
            'start_time': None,
            'end_time': None,
            'steps': [],
            'initial_rows': 0,
            'final_rows': 0,
            'rows_removed': 0
        }

    def read_raw_data(self):
        logger.info(f"Reading raw data from: {self.raw_csv}")
        if not Path(self.raw_csv).exists():
            raise FileNotFoundError(f"Raw CSV file not found: {self.raw_csv}")
        self.df = pd.read_csv(self.raw_csv, low_memory=False)
        self.cleaning_report['initial_rows'] = len(self.df)
        logger.info(f"Loaded {len(self.df)} rows and {len(self.df.columns)} columns")
        self._record_step('read_raw_data', rows_before=0, rows_after=len(self.df), description='Read raw CSV data')

    def standardize_text_columns(self):
        if self.df is None:
            return
        logger.info("Standardizing text columns...")
        rows_before = len(self.df)
        # Trim and normalize text fields
        text_cols = ['address', 'street_name', 'city', 'state', 'postcode', 'property_type', 'agency_name']
        for col in text_cols:
            if col in self.df.columns:
                self.df[col] = self.df[col].astype(str).str.strip()
                self.df.loc[self.df[col].isin(['', 'nan', 'NaN', 'None', 'null', 'NULL']), col] = np.nan

        # Clean postcode values
        def clean_postcode(val):
            if pd.isna(val):
                return np.nan
            s = str(val).strip()
            if s.endswith('.0'):
                s = s[:-2]
            if s in ['', 'nan', 'NaN', 'None', 'null', 'NULL']:
                return np.nan
            if s.isdigit() and len(s) < 5:
                s = s.zfill(5)
            return s

        if 'postcode' in self.df.columns:
            self.df['postcode'] = self.df['postcode'].apply(clean_postcode)
            logger.info("Cleaned postcode values")

            # Try extracting postcode from address before mode imputation
            def extract_postcode_from_address(row):
                postcode = row['postcode']
                if pd.notna(postcode):
                    return postcode
                addr = str(row['address'])
                match = re.search(r'\b(?:[A-Z]{2}\s+)?(\d{5})\b$', addr)
                if match:
                    return match.group(1)
                return np.nan

            self.df['postcode'] = self.df.apply(extract_postcode_from_address, axis=1)
            logger.info("Extracted postcodes from addresses")

            # Impute postcode by city/state mode
            if 'city' in self.df.columns and 'state' in self.df.columns:
                mode_postcode = self.df.groupby(['city', 'state'])['postcode'].transform(
                    lambda x: x.fillna(x.mode()[0] if len(x.mode()) > 0 else np.nan)
                )
                self.df['postcode'] = self.df['postcode'].fillna(mode_postcode)
                logger.info("Imputed missing postcodes using city/state mode")

        # Standardize property_type casing (Title Case)
        if 'property_type' in self.df.columns:
            self.df['property_type'] = self.df['property_type'].str.title()
        
        self._record_step('standardize_text_columns', rows_before=rows_before, rows_after=len(self.df), description='Standardized text columns, cleaned postcodes, extracted postcodes from addresses, imputed missing postcodes')

    def coerce_core_types(self):
        if self.df is None:
            return
        logger.info("Coercing core data types...")
        rows_before = len(self.df)
        # Numeric coercions
        num_cols = ['price', 'bedroom_number', 'bathroom_number', 'living_space', 'land_space', 'latitude', 'longitude']
        for col in num_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')

        # RunDate date formatting
        if 'RunDate' in self.df.columns:
            self.df['RunDate'] = pd.to_datetime(self.df['RunDate'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        self._record_step('coerce_core_types', rows_before=rows_before, rows_after=len(self.df), description='Coerced numeric columns and formatted RunDate')

    def null_invalid_values(self):
        if self.df is None:
            return
        logger.info("Nullifying invalid values...")
        rows_before = len(self.df)
        # Nullify impossible numeric values before imputation
        if 'price' in self.df.columns:
            invalid_price = (self.df['price'] <= 0).sum()
            self.df.loc[self.df['price'] <= 0, 'price'] = np.nan
            logger.info(f"Nullified {invalid_price} invalid price values")
        if 'latitude' in self.df.columns:
            invalid_lat = ((self.df['latitude'] < -90) | (self.df['latitude'] > 90) | (self.df['latitude'] == 0)).sum()
            self.df.loc[(self.df['latitude'] < -90) | (self.df['latitude'] > 90) | (self.df['latitude'] == 0), 'latitude'] = np.nan
            logger.info(f"Nullified {invalid_lat} invalid latitude values")
        if 'longitude' in self.df.columns:
            invalid_lon = ((self.df['longitude'] < -180) | (self.df['longitude'] > 180) | (self.df['longitude'] == 0)).sum()
            self.df.loc[(self.df['longitude'] < -180) | (self.df['longitude'] > 180) | (self.df['longitude'] == 0), 'longitude'] = np.nan
            logger.info(f"Nullified {invalid_lon} invalid longitude values")
        if 'bedroom_number' in self.df.columns:
            invalid_bed = (self.df['bedroom_number'] < 0).sum()
            self.df.loc[self.df['bedroom_number'] < 0, 'bedroom_number'] = np.nan
            logger.info(f"Nullified {invalid_bed} invalid bedroom values")
        if 'bathroom_number' in self.df.columns:
            invalid_bath = (self.df['bathroom_number'] < 0).sum()
            self.df.loc[self.df['bathroom_number'] < 0, 'bathroom_number'] = np.nan
            logger.info(f"Nullified {invalid_bath} invalid bathroom values")
        if 'living_space' in self.df.columns:
            invalid_living = (self.df['living_space'] <= 0).sum()
            self.df.loc[self.df['living_space'] <= 0, 'living_space'] = np.nan
            logger.info(f"Nullified {invalid_living} invalid living_space values")
        if 'land_space' in self.df.columns:
            invalid_land = (self.df['land_space'] <= 0).sum()
            self.df.loc[self.df['land_space'] <= 0, 'land_space'] = np.nan
            logger.info(f"Nullified {invalid_land} invalid land_space values")
        
        self._record_step('null_invalid_values', rows_before=rows_before, rows_after=len(self.df), description='Nullified impossible/invalid numeric values')

    def convert_land_measurements(self):
        if self.df is None:
            return
        logger.info("Converting land measurements to square feet...")
        rows_before = len(self.df)
        # Converted land measurements to land_space_sqft before imputing comparable land size
        self.df['land_space_sqft'] = np.nan
        if 'land_space' in self.df.columns and 'land_space_unit' in self.df.columns:
            acres_mask = self.df['land_space_unit'] == 'acres'
            sqft_mask = self.df['land_space_unit'] == 'sqft'
            acres_count = acres_mask.sum()
            sqft_count = sqft_mask.sum()
            self.df.loc[acres_mask, 'land_space_sqft'] = self.df.loc[acres_mask, 'land_space'] * 43560
            self.df.loc[sqft_mask, 'land_space_sqft'] = self.df.loc[sqft_mask, 'land_space']
            logger.info(f"Converted {acres_count} acres to sqft, {sqft_count} sqft records kept as-is")
        
        self._record_step('convert_land_measurements', rows_before=rows_before, rows_after=len(self.df), description='Converted land measurements to square feet')

    def derive_missing_location_text(self):
        if self.df is None:
            return
        logger.info("Deriving missing location text...")
        rows_before = len(self.df)
        # Combine address components into address if missing
        if 'address' in self.df.columns:
            mask = self.df['address'].isnull() | (self.df['address'].astype(str).str.strip() == '')
            missing_count = mask.sum()
            parts = [c for c in ['street_name', 'city', 'state', 'postcode'] if c in self.df.columns]
            parts = [c for c in ['street_name', 'city', 'state', 'postcode'] if c in self.df.columns]
            self.df.loc[mask, 'address'] = self.df.loc[mask, parts].astype(str).apply(
                lambda r: ' '.join([p for p in r if p and p != 'nan']), axis=1
            )
            logger.info(f"Derived addresses for {missing_count} missing records")
        
        self._record_step('derive_missing_location_text', rows_before=rows_before, rows_after=len(self.df), description='Derived missing location text from components')

    def fill_group_median(self):
        if self.df is None:
            return
        logger.info("Filling missing values with group medians...")
        rows_before = len(self.df)
        # Fill land-listing bedrooms, bathrooms, and living space with 0 where appropriate
        if 'property_type' in self.df.columns:
            lot_mask = self.df['property_type'].str.upper() == 'LOT'
            lot_count = lot_mask.sum()
            for col in ['bedroom_number', 'bathroom_number', 'living_space']:
                if col in self.df.columns:
                    self.df.loc[lot_mask, col] = self.df.loc[lot_mask, col].fillna(0)
            logger.info(f"Filled LOT property numeric fields with 0 for {lot_count} records")

        # Fill remaining numeric gaps with property-type/state medians, then broader medians
        numeric_cols = ['bedroom_number', 'bathroom_number', 'living_space', 'land_space_sqft']
        numeric_cols = [c for c in numeric_cols if c in self.df.columns]

        if 'property_type' in self.df.columns and 'state' in self.df.columns:
            for col in numeric_cols:
                grouped = self.df.groupby(['property_type', 'state'])[col].transform('median')
                self.df[col] = self.df[col].fillna(grouped)
            logger.info("Filled missing values using property_type/state median")

        if 'property_type' in self.df.columns:
            for col in numeric_cols:
                grouped = self.df.groupby('property_type')[col].transform('median')
                self.df[col] = self.df[col].fillna(grouped)
            logger.info("Filled remaining missing values using property_type median")

        for col in numeric_cols:
            self.df[col] = self.df[col].fillna(self.df[col].median())
        logger.info("Filled final missing values using global median")
        
        self._record_step('fill_group_median', rows_before=rows_before, rows_after=len(self.df), description='Filled missing numeric values with group medians')

    def fill_coordinates(self):
        if self.df is None:
            return
        logger.info("Filling missing coordinates...")
        rows_before = len(self.df)
        # Fill missing coordinates using postcode, city/state, then state medians
        coords = ['latitude', 'longitude']
        coords = [c for c in coords if c in self.df.columns]
        if not coords:
            return

        if 'postcode' in self.df.columns:
            missing_before = self.df[coords].isnull().sum().sum()
            postcode_coords = self.df.groupby('postcode')[coords].median()
            self.df = self.df.join(postcode_coords, on='postcode', rsuffix='_postcode')
            for c in coords:
                self.df[c] = self.df[c].fillna(self.df[c + '_postcode'])
            self.df.drop(columns=[c + '_postcode' for c in coords], inplace=True)
            missing_after = self.df[coords].isnull().sum().sum()
            logger.info(f"Filled {missing_before - missing_after} coordinates using postcode median")

        if 'city' in self.df.columns and 'state' in self.df.columns:
            missing_before = self.df[coords].isnull().sum().sum()
            city_state_coords = self.df.groupby(['city', 'state'])[coords].median()
            self.df = self.df.join(city_state_coords, on=['city', 'state'], rsuffix='_city_state')
            for c in coords:
                self.df[c] = self.df[c].fillna(self.df[c + '_city_state'])
            self.df.drop(columns=[c + '_city_state' for c in coords], inplace=True)
            missing_after = self.df[coords].isnull().sum().sum()
            logger.info(f"Filled {missing_before - missing_after} coordinates using city/state median")

        if 'state' in self.df.columns:
            missing_before = self.df[coords].isnull().sum().sum()
            state_coords = self.df.groupby('state')[coords].median()
            self.df = self.df.join(state_coords, on='state', rsuffix='_state')
            for c in coords:
                self.df[c] = self.df[c].fillna(self.df[c + '_state'])
            self.df.drop(columns=[c + '_state' for c in coords], inplace=True)
            missing_after = self.df[coords].isnull().sum().sum()
            logger.info(f"Filled {missing_before - missing_after} coordinates using state median")
        
        self._record_step('fill_coordinates', rows_before=rows_before, rows_after=len(self.df), description='Filled missing coordinates using postcode, city/state, and state medians')

    def add_engineered_fields(self):
        if self.df is None:
            return
        logger.info("Adding engineered fields...")
        rows_before = len(self.df)
        # Calculate price_per_unit = price / living_space if living_space > 0 else land_space_sqft
        if 'price' in self.df.columns and 'living_space' in self.df.columns and 'land_space_sqft' in self.df.columns:
            self.df['price_per_unit'] = self.df['price'] / self.df['living_space']
            lot_or_zero_living = (self.df['living_space'] == 0) | self.df['living_space'].isnull()
            self.df.loc[lot_or_zero_living, 'price_per_unit'] = self.df.loc[lot_or_zero_living, 'price'] / self.df.loc[lot_or_zero_living, 'land_space_sqft']
            self.df['price_per_unit'] = self.df['price_per_unit'].replace([np.inf, -np.inf], np.nan).fillna(0)
            logger.info("Calculated price_per_unit field")

        # Fill text field gaps
        if 'street_name' in self.df.columns:
            missing_street = self.df['street_name'].isnull().sum()
            self.df['street_name'] = self.df['street_name'].fillna('Unknown')
            logger.info(f"Filled {missing_street} missing street_name values with 'Unknown'")
        if 'agency_name' in self.df.columns:
            missing_agency = self.df['agency_name'].isnull().sum()
            self.df['agency_name'] = self.df['agency_name'].fillna('Unknown')
            logger.info(f"Filled {missing_agency} missing agency_name values with 'Unknown'")

        # Fill missing land_space and land_space_unit
        if 'land_space' in self.df.columns and 'land_space_sqft' in self.df.columns:
            missing_land = self.df['land_space'].isnull().sum()
            self.df['land_space'] = self.df['land_space'].fillna(self.df['land_space_sqft'])
            logger.info(f"Filled {missing_land} missing land_space values with land_space_sqft")
        if 'land_space_unit' in self.df.columns:
            missing_unit = self.df['land_space_unit'].isnull().sum()
            self.df['land_space_unit'] = self.df['land_space_unit'].fillna('sqft')
            logger.info(f"Filled {missing_unit} missing land_space_unit values with 'sqft'")
        
        self._record_step('add_engineered_fields', rows_before=rows_before, rows_after=len(self.df), description='Added price_per_unit and filled text field gaps')

    def finalize_dataset(self):
        if self.df is None:
            return
        logger.info("Finalizing dataset...")
        rows_before = len(self.df)
        # Remove duplicate property IDs
        if 'property_id' in self.df.columns:
            dup_count = self.df['property_id'].duplicated().sum()
            self.df = self.df.drop_duplicates(subset=['property_id'])
            logger.info(f"Removed {dup_count} duplicate property IDs")

        # Drop rows still missing production-critical identifiers, location, price, or coordinates
        critical_cols = ['property_id', 'price', 'postcode', 'city', 'state', 'latitude', 'longitude']
        critical_cols = [c for c in critical_cols if c in self.df.columns]
        if critical_cols:
            critical_mask = self.df[critical_cols].isnull().any(axis=1)
            critical_count = critical_mask.sum()
            self.df = self.df[~critical_mask]
            logger.info(f"Removed {critical_count} rows missing critical fields")

        # Select columns to retain in final cleaned structure
        columns_to_keep = [
            'property_id', 'property_url', 'address', 'street_name', 'city', 'state', 'postcode',
            'latitude', 'longitude', 'price', 'bedroom_number', 'bathroom_number', 'price_per_unit',
            'living_space', 'land_space', 'land_space_unit', 'land_space_sqft', 'property_type',
            'property_status', 'RunDate', 'agency_name', 'is_owned_by_zillow'
        ]
        columns_before = len(self.df.columns)
        columns_to_keep = [c for c in columns_to_keep if c in self.df.columns]
        self.df = self.df[columns_to_keep]
        logger.info(f"Selected {len(columns_to_keep)} columns (removed {columns_before - len(columns_to_keep)} columns)")
        
        self._record_step('finalize_dataset', rows_before=rows_before, rows_after=len(self.df), description=f'Removed duplicates, dropped {critical_count} rows with missing critical fields, selected final columns')

    def _record_step(self, step_name: str, rows_before: int, rows_after: int, description: str):
        self.cleaning_report['steps'].append({
            'step': step_name,
            'description': description,
            'rows_before': rows_before,
            'rows_after': rows_after,
            'rows_removed': rows_before - rows_after
        })

    def summarize(self) -> dict:
        if self.df is None:
            return {}
        return {
            'rows': len(self.df),
            'columns': list(self.df.columns),
            'null_counts': self.df.isnull().sum().to_dict(),
        }

    def save_cleaning_report(self, report_path: Optional[str] = None):
        if report_path is None:
            data_dir = Path(__file__).resolve().parents[2] / 'data'
            report_path = data_dir / 'cleaning_report.json'
        
        self.cleaning_report['end_time'] = datetime.now().isoformat()
        self.cleaning_report['final_rows'] = len(self.df) if self.df is not None else 0
        self.cleaning_report['rows_removed'] = self.cleaning_report['initial_rows'] - self.cleaning_report['final_rows']
        self.cleaning_report['final_columns'] = list(self.df.columns) if self.df is not None else []
        self.cleaning_report['final_null_counts'] = self.df.isnull().sum().to_dict() if self.df is not None else {}
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.cleaning_report, f, indent=2)
        
        logger.info(f"Cleaning report saved to: {report_path}")
        return self.cleaning_report

    def clean_dataset(self):
        self.cleaning_report['start_time'] = datetime.now().isoformat()
        logger.info("Starting data cleaning pipeline...")
        self.read_raw_data()
        self.standardize_text_columns()
        self.coerce_core_types()
        self.null_invalid_values()
        self.convert_land_measurements()
        self.derive_missing_location_text()
        self.fill_group_median()
        self.fill_coordinates()
        self.add_engineered_fields()
        self.finalize_dataset()
        logger.info(f"Data cleaning pipeline completed. Final rows: {len(self.df) if self.df is not None else 0}")

    def clean(self, sample_size: Optional[int] = None) -> pd.DataFrame:
        self.cleaning_report['start_time'] = datetime.now().isoformat()
        logger.info("Starting data cleaning pipeline...")
        self.read_raw_data()
        if sample_size:
            self.df = self.df.sample(n=sample_size, random_state=42)
            logger.info(f"Sampled {sample_size} rows from dataset")
        self.standardize_text_columns()
        self.coerce_core_types()
        self.null_invalid_values()
        self.convert_land_measurements()
        self.derive_missing_location_text()
        self.fill_group_median()
        self.fill_coordinates()
        self.add_engineered_fields()
        self.finalize_dataset()
        logger.info(f"Data cleaning pipeline completed. Final rows: {len(self.df) if self.df is not None else 0}")
        return self.df.copy()


if __name__ == '__main__':
    cleaner = CleanDataset()
    df = cleaner.clean(sample_size=None)
    cleaner.save_cleaning_report()
    print('Cleaned dataset row count:', len(df))
    print(df.isnull().sum())
