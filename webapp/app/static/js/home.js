document.addEventListener('DOMContentLoaded', (event) => {
    const addButton = document.querySelector('.add-field-button'); // Button to add new field row
    const fieldsContainer = document.getElementById('fields'); // Container to hold new fields
    const originalSelect = document.getElementById('field-type'); // Original select element

    // Function to create a new field row
    function addFieldRow() {
        // Increment a counter or use a timestamp for a unique field name suffix
        const uniqueId = Date.now();

        // Clone the original select element
        let newSelect = originalSelect.cloneNode(true);
        newSelect.name = `field_type_${uniqueId}`; // Give the select a new unique name
        newSelect.id = `field-type-${uniqueId}`; // Give the select a new unique ID

        // Create the new input for the custom name
        let newInput = document.createElement('input');
        newInput.type = 'text';
        newInput.name = `custom_name_${uniqueId}`;
        newInput.classList.add('form-control');
        newInput.placeholder = 'Enter field custom name';

        // Create a delete button for the new row
        let deleteButton = document.createElement('button');
        deleteButton.type = 'button';
        deleteButton.innerText = 'X';
        deleteButton.classList.add('btn', 'btn-danger', 'delete-field-button');

        // Create a new DIV for the form-row and add the cloned select and new input
        let newRow = document.createElement('div');
        newRow.classList.add('form-row');

        // Create DIVs for layout and append the select and input elements
        let selectDiv = document.createElement('div');
        selectDiv.classList.add('form-group', 'col-md-2');
        selectDiv.appendChild(newSelect);

        let inputDiv = document.createElement('div');
        inputDiv.classList.add('form-group', 'col-md-4');
        inputDiv.appendChild(newInput);

        let deleteDiv = document.createElement('div');
        deleteDiv.classList.add('form-group', 'col-md-1');
        deleteDiv.appendChild(deleteButton);

        // Append the layout DIVs to the form-row
        newRow.appendChild(selectDiv);
        newRow.appendChild(inputDiv);
        newRow.appendChild(deleteDiv);

        // Append the new row to the fields container
        fieldsContainer.appendChild(newRow);
    }

    // Event listener for the Add button
    addButton.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent form submission
        addFieldRow(); // Add a new row of fields
    });

    const form = document.getElementById('data-form');

    form.addEventListener('click', function(event) {
        // Check if the clicked element has the class 'delete-field-button'
        if (event.target.classList.contains('delete-field-button')) {
            // Remove the closest .form-row element
            event.target.closest('.form-row').remove();
        }
    });

    form.addEventListener('submit', function(event) {
        let isValid = true;
        const rows = document.getElementById('rows');
        const fileName = document.getElementById('file-name');
        const fieldType = document.getElementById('field-type');

        // Validate number of rows (must be a number and greater than 0)
        if (!rows.value || isNaN(rows.value) || parseInt(rows.value) <= 0) {
            alert('Please enter a valid number of rows.');
            isValid = false;
        }

        // Validate file name (must not be empty)
        if (!fileName.value.trim()) {
            alert('Please enter a file name.');
            isValid = false;
        }

        // Validate field type (must be selected)
        if (!fieldType.value) {
            alert('Please select a field type.');
            isValid = false;
        }

        // If validation fails, prevent form submission
        if (!isValid) {
            event.preventDefault();
        }
    });

    document.getElementById('download-btn').addEventListener('click', function() {
        form.action = '/download';
    });
    document.getElementById('preview-btn').addEventListener('click', function() {
        form.action = '/preview';
    });
    document.getElementById('cloudUpload-btn').addEventListener('click', function() {
        const formData = new FormData(form);
        const requestData = {};

        for (const [key, value] of formData.entries()) {
            requestData[key] = value;
        }

        fetch('/upload-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            // Update the webpage with the success message
            const uploadStatusDiv = document.getElementById('uploadStatus');
            uploadStatusDiv.innerHTML = `Upload to Google Cloud successful under filename "${data.filename}"`;
            // On success
            uploadStatusDiv.className = 'success';
            uploadStatusDiv.style.display = 'block';
        })
        .catch((error) => {
            console.error('Error:', error);
            const uploadStatusDiv = document.getElementById('uploadStatus');
            uploadStatusDiv.innerHTML = `Error during upload: ${error}`;
            // On error
            uploadStatusDiv.className = 'error';
            uploadStatusDiv.style.display = 'block';
        });

        event.preventDefault();
    });
    document.getElementById('cloudDownload-btn').addEventListener('click', function() {
        form.action = '/cloudDownload';
    });


});
