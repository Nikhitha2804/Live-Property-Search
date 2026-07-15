let dataTable;

$(document).ready(function () {
  dataTable = $('#resultsTable').DataTable({
    pageLength: 25,
    paging: true,
    searching: false,
    info: true,
    order: [[5, 'asc']], // Initial sort on Price
    dom: 'rt<"bottom"ip>',
    columnDefs: [
      {
        targets: 5, // Price column
        orderable: true,
        render: function (data, type) {
          if (type === 'display' && data) {
            return '$' + parseFloat(data).toLocaleString();
          }
          return data;
        }
      },
      {
        targets: 9, // Living Space column
        orderable: false,
        render: function (data, type) {
          if (type === 'display' && data) {
            return parseFloat(data).toLocaleString() + ' sq ft';
          }
          return data;
        }
      },
      {
        targets: '_all',
        orderable: false // Disable sorting for all except Price
      }
    ]
  });

  // Load all properties on page load
  loadAllProperties();

  $('#searchForm').on('submit', function (e) {
    e.preventDefault();
    performSearch();
  });

  // Clear advanced filters only (not the search input)
$('#clearFiltersBtn').on('click', function () {
  // Clear only advanced filter fields
  $('#min_price').val('');
  $('#max_price').val('');
  $('#min_bedrooms').val('');
  $('#property_type').val('');

  // Collapse the advanced filters section
  $('#advancedFilters').collapse('hide');

  // Reload all properties
  loadAllProperties();
});

  $('#searchInput').focus();

  $('#searchInput').on('keypress', function (e) {
    if (e.which === 13) {
      e.preventDefault();
      $('#searchForm').submit();
    }
  });

  // Show/Hide search/clear buttons when filters expand/collapse
  const filtersCollapse = document.getElementById('advancedFilters');
  const searchButtons = document.getElementById('searchButtons');

  filtersCollapse.addEventListener('shown.bs.collapse', function () {
    searchButtons.style.display = 'block';
  });

  filtersCollapse.addEventListener('hidden.bs.collapse', function () {
    searchButtons.style.display = 'none';
  });
});

function loadAllProperties() {
  $('.loading').show();
  $('#resultsSection').hide();

  $.ajax({
    url: '/api/properties',
    method: 'GET',
    success: function (response) {
      if (response.success) {
        displayResults(response.data);
        $('#filtersToggleWrapper').show();
      } else {
        alert('Error: ' + response.error);
      }
    },
    error: function (xhr, status, error) {
      alert('Error loading properties: ' + error);
    },
    complete: function () {
      $('.loading').hide();
    }
  });
}

function performSearch() {
  const searchValue = $('#searchInput').val().trim();
  const minPrice = $('#min_price').val();
  const maxPrice = $('#max_price').val();
  const minBedrooms = $('#min_bedrooms').val();
  const propertyType = $('#property_type').val();

  // Check if any filter is applied
  const hasFilters = searchValue || minPrice || maxPrice || minBedrooms || propertyType;

  if (!hasFilters) {
    alert('Please enter a search term or use advanced filters.');
    return;
  }

  $('#resultsSection').hide();
  $('.loading').show();
  const $buttons = $('#searchForm').find('button');
  $buttons.prop('disabled', true);

  const formData = {
    search: searchValue,
    min_price: minPrice,
    max_price: maxPrice,
    min_bedrooms: minBedrooms,
    property_type: propertyType
  };

  $.ajax({
    url: '/api/search',
    method: 'POST',
    contentType: 'application/json',
    data: JSON.stringify(formData),
    success: function (response) {
      if (response.success) {
        displayResults(response.data);
        $('#filtersToggleWrapper').show(); // Show filter toggle after results
      } else {
        alert('Error: ' + response.error);
      }
    },
    error: function (xhr) {
      let message = xhr.responseJSON && xhr.responseJSON.error
        ? xhr.responseJSON.error
        : xhr.statusText || 'Unknown error';
      alert('Error searching properties: ' + message);
    },
    complete: function () {
      $('.loading').hide();
      $buttons.prop('disabled', false);
    }
  });
}
function displayResults(data) {
  dataTable.clear().draw();

  if (data.length === 0) {
    dataTable.row.add([
      '',
      'No properties found matching your criteria.',
      '',
      '',
      '',
      '',
      '',
      '',
      '',
      '',
      ''
    ]).draw();
    $('#resultsSection').show();
    return;
  }

  data.forEach(function (property) {
    const row = [
      property.property_id || '',
      property.address || '',
      property.city || '',
      property.state || '',
      property.postcode || '',
      property.price || 0,
      property.bedroom_number || 0,
      property.bathroom_number || 0,
      property.property_type || '',
      property.living_space || 0,
      `<button class="btn btn-sm btn-dark" onclick="viewProperty('${property.property_id}')"><i class="bi bi-eye"></i> View</button>`
    ];
    dataTable.row.add(row);
  });

  dataTable.draw();

  $('#resultsSection').show();
}
window.viewProperty = function(propertyId) {
  $('#propertyDetails').html('<div class="text-center p-4"><div class="spinner-border text-primary"></div></div>');
  $('#propertyModal').modal('show');

  $.ajax({
    url: `/api/property/${propertyId}`,
    method: 'GET',
    success: function (response) {
      if (response.success && response.data) {
        displayPropertyDetails(response.data);
      } else {
        $('#propertyDetails').html('<div class="alert alert-danger">Error loading property details.</div>');
      }
    },
    error: function (xhr, status, error) {
      $('#propertyDetails').html('<div class="alert alert-danger">Error fetching property details: ' + error + '</div>');
    }
  });
};

function displayPropertyDetails(property) {
  let html = '<div class="row">';
  html += '<div class="col-md-6">';
  html += '<h6 class="text-primary mb-3"><i class="bi bi-info-circle"></i> Basic Information</h6>';
  html += '<table class="table table-sm">';
  html += `<tr><td><strong>Property ID:</strong></td><td>${property.property_id || 'N/A'}</td></tr>`;
  html += `<tr><td><strong>Address:</strong></td><td>${property.address || 'N/A'}</td></tr>`;
  html += `<tr><td><strong>Street Name:</strong></td><td>${property.street_name || 'N/A'}</td></tr>`;
  html += `<tr><td><strong>City:</strong></td><td>${property.city || 'N/A'}</td></tr>`;
  html += `<tr><td><strong>State:</strong></td><td>${property.state || 'N/A'}</td></tr>`;
  html += `<tr><td><strong>Postcode:</strong></td><td>${property.postcode || 'N/A'}</td></tr>`;
  html += '</table></div>';

  html += '<div class="col-md-6">';
  html += '<h6 class="text-primary mb-3"><i class="bi bi-house"></i> Property Details</h6>';
  html += '<table class="table table-sm">';
  html += `<tr><td><strong>Price:</strong></td><td class="text-success fw-bold">$${property.price ? property.price.toLocaleString() : 'N/A'}</td></tr>`;
  html += `<tr><td><strong>Bedrooms:</strong></td><td>${property.bedroom_number || 'N/A'}</td></tr>`;
  html += `<tr><td><strong>Bathrooms:</strong></td><td>${property.bathroom_number || 'N/A'}</td></tr>`;
  html += `<tr><td><strong>Property Type:</strong></td><td>${property.property_type || 'N/A'}</td></tr>`;
  html += `<tr><td><strong>Status:</strong></td><td>${property.property_status || 'N/A'}</td></tr>`;
  html += '</table></div>';

  html += '<div class="col-12 mt-3">';
  html += '<h6 class="text-primary mb-3"><i class="bi bi-rulers"></i> Additional Information</h6>';
  html += '<table class="table table-sm">';
  html += `<tr><td><strong>Living Space:</strong></td><td>${property.living_space ? property.living_space.toLocaleString() + ' sq ft' : 'N/A'}</td></tr>`;
  html += `<tr><td><strong>Land Space:</strong></td><td>${property.land_space ? property.land_space.toLocaleString() + ' ' + (property.land_space_unit || 'sq ft') : 'N/A'}</td></tr>`;
  html += `<tr><td><strong>Price per Unit:</strong></td><td>${property.price_per_unit ? '$' + property.price_per_unit.toLocaleString() : 'N/A'}</td></tr>`;
  html += `<tr><td><strong>Agency:</strong></td><td>${property.agency_name || 'N/A'}</td></tr>`;
  html += `<tr><td><strong>Owned by Zillow:</strong></td><td>${property.is_owned_by_zillow ? 'Yes' : 'No'}</td></tr>`;
  html += `<tr><td><strong>Run Date:</strong></td><td>${property.RunDate || 'N/A'}</td></tr>`;
  html += '</table></div>';

  if (property.latitude && property.longitude) {
    html += '<div class="col-12 mt-3">';
    html += '<h6 class="text-primary mb-3"><i class="bi bi-geo-alt"></i> Location</h6>';
    html += '<table class="table table-sm">';
    html += `<tr><td><strong>Coordinates:</strong></td><td>${property.latitude}, ${property.longitude}</td></tr>`;
    html += '</table></div>';
  }

  if (property.property_url) {
    html += '<div class="col-12 mt-3 text-center">';
    html += `<a href="${property.property_url}" target="_blank" class="btn btn-primary">
                <i class="bi bi-box-arrow-up-right"></i> View on Original Site
             </a>`;
    html += '</div>';
  }

  html += '</div>';
  $('#propertyDetails').html(html);
}