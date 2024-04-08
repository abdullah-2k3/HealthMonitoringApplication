function fetchData() {
  return fetch("/patient-data")
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json(); // Parse JSON response
    })
    .then((json) => {
      // Check if the response contains valid data
      if (!Array.isArray(json.data)) {
        throw new Error("Invalid data format");
      }
      // Process the fetched data
      displayData(json);
      displayChart(json.data);
    })
    .catch((error) => {
      console.error("Error fetching data:", error);
    });
}

function displayData(json) {
  // Extract column headers and data from JSON response
  var columns = json.columns;
  var data = json.data;

  // Clear existing content (if any)
  var container = document.getElementById("data-container");
  container.innerHTML = "";

  // Create cards for each value
  data.forEach((row) => {
    // Iterate through each column
    columns.forEach((column) => {
      // Create card element
      var card = document.createElement("div");
      card.classList.add("col-12", "col-md-4", "mb-4"); // Bootstrap column classes

      // Create card body
      var cardBody = document.createElement("div");
      cardBody.classList.add("card", "shadow-sm");

      // Create card content
      var cardContent = document.createElement("div");
      cardContent.classList.add("card-body");

      // Add column name as card title
      var cardTitle = document.createElement("h5");
      cardTitle.classList.add("card-title");
      cardTitle.textContent = column;
      cardContent.appendChild(cardTitle);

      // Add value to card content
      var value = document.createElement("p");
      value.textContent = row[column];
      cardContent.appendChild(value);

      cardBody.appendChild(cardContent);
      card.appendChild(cardBody);
      container.appendChild(card);
    });
  });
}

function displayChart(data) {
  // Check if data is an array
  if (!Array.isArray(data)) {
    console.error("Data is not an array:", data);
    return;
  }

  var ctx = document.getElementById("health-chart").getContext("2d");

  // Extract relevant data for the chart
  var labels = data.map((item, index) => `Patient ${index + 1}`);
  var heightData = data.map((item) => item.Height);
  var weightData = data.map((item) => item.Weight);
  var bmiData = data.map((item) => calculateBMI(item.Height, item.Weight));

  // Ensure all required data is available
  if (
    !labels.length ||
    !heightData.length ||
    !weightData.length ||
    !bmiData.length
  ) {
    console.error("Incomplete data:", labels, heightData, weightData, bmiData);
    return;
  }

  var chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Height (cm)",
          data: heightData,
          borderColor: "rgba(75, 192, 192, 1)",
          backgroundColor: "rgba(75, 192, 192, 0.2)",
          borderWidth: 1,
        },
        {
          label: "Weight (kg)",
          data: weightData,
          borderColor: "rgba(255, 99, 132, 1)",
          backgroundColor: "rgba(255, 99, 132, 0.2)",
          borderWidth: 1,
        },
        {
          label: "BMI",
          data: bmiData,
          borderColor: "rgba(54, 162, 235, 1)",
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          borderWidth: 1,
        },
      ],
    },
    options: {
      scales: {
        yAxes: [
          {
            ticks: {
              beginAtZero: true,
            },
          },
        ],
      },
    },
  });
}

// Call displayChart function with data when page loads
window.onload = function () {
  fetchData()
    .then((data) => {
      displayData(data);
      displayChart(data);
    })
    .catch((error) => {
      console.error("Error fetching data:", error);
    });
};

function calculateBMI(height, weight) {
  // Convert height to meters
  var heightInMeters = height / 100;

  // Calculate BMI
  var bmi = weight / (heightInMeters * heightInMeters);

  // Round BMI to two decimal places
  return bmi.toFixed(2);
}

function populateTableWithData(data) {
  const tableBody = document.getElementById("data-table");
  if (tableBody) {
    tableBody.innerHTML = "";
    data.forEach((item) => {
      const row = `
        <tr>
          <td>${item.name}</td>
          <td>${item.age}</td>
          <td>${item.education}</td>
          <td>${item.job}</td>
        </tr>`;
      tableBody.innerHTML += row;
    });
  }
}

fetchData().then((data) => {
  populateTableWithData(data);
});

// Function to load page
function loadPage(page, pageTitle, pageUrl) {
  window.location.href = pageUrl;
}

// Fade out flash messages after 3 seconds
document.addEventListener("DOMContentLoaded", function () {
  var alerts = document.querySelectorAll(".alert");
  alerts.forEach(function (alert) {
    setTimeout(function () {
      alert.style.transition = "opacity 1s";
      alert.style.opacity = 0;
      setTimeout(function () {
        alert.remove();
      }, 1000);
    }, 3000); // 3 seconds
  });
});

function setAction(action) {
  document.getElementById("action").value = action;

  document.querySelector("form").submit();
}

function showPassword() {
  var x = document.getElementById("password");
  if (x.type === "password") {
    x.type = "text";
  } else {
    x.type = "password";
  }
}

function validateForm() {
  var username = document.getElementById("username").value;
  var password = document.getElementById("pwd").value;
  if (!username || !password) {
    alert("Please enter both username and password.");
    return false;
  }
  return true;
}

function updateLocations() {
  var doctor = document.getElementById("doctor").value;
  var locations = document.getElementById("location");
  locations.innerHTML = ""; // Clear existing options
  if (doctor) {
    // Make AJAX request to get locations for the selected doctor
    fetch("/get_locations?doctor=" + doctor)
      .then((response) => response.json())
      .then((data) => {
        // Populate locations dropdown with options
        data.locations.forEach((location) => {
          var option = document.createElement("option");
          option.text = location;
          option.value = location;
          locations.add(option);
        });
      })
      .catch((error) => console.error("Error fetching locations:", error));
  }
}
