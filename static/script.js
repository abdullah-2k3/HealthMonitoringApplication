function calculateBMI(height, weight) {
  // Convert height to meters
  var heightInMeters = height / 100;

  // Calculate BMI
  var bmi = weight / (heightInMeters * heightInMeters);

  // Round BMI to two decimal places
  return bmi.toFixed(2);
}

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

function cancelAppointment() {
  const popup = document.getElementById("confirmation-popup");
  popup.style.display = "block";

  const confirmButton = document.getElementById("confirm-button");
  confirmButton.addEventListener("click", function () {
    const form = document.getElementById("cancel-appointment-form");
    form.submit();

    // Hide the pop-up
    popup.style.display = "none";
  });

  // Handle the cancel button click
  const cancelButton = document.getElementById("cancel-button");
  cancelButton.addEventListener("click", function () {
    // Hide the pop-up
    popup.style.display = "none";
  });
}

function ToggleNav() {
  var sidebar = document.getElementById("mySidebar");
  if (sidebar.style.width == "0px") {
    openNav();
  } else {
    closeNav();
  }
}

function openNav() {
  document.getElementById("mySidebar").style.width = "200px";
  document.getElementById("mySidebar").style.padding = "10px";
  document.querySelector(".sidebar-image").style.display = "block";
  document.getElementById("my_header").style.marginLeft = "0px";
  document.getElementById("main-content").style.marginLeft = "0px";

  var sidebarButtons = document.querySelectorAll(".sidebar button");
  sidebarButtons.forEach(function (button) {
    button.style.display = "block";
  });
}

function closeNav() {
  document.getElementById("my_header").style.marginLeft = "-200px";
  document.getElementById("mySidebar").style.width = "0px";
  document.getElementById("mySidebar").style.padding = "0";
  document.querySelector(".sidebar-image").style.display = "none";
  document.getElementById("main-content").style.marginLeft = "-205px";

  var sidebarButtons = document.querySelectorAll(".sidebar button");
  sidebarButtons.forEach(function (button) {
    button.style.paddingleft = "0px";
    button.style.display = "none";
  });
}

function getDate() {
  var currentDate = new Date();
  var year = currentDate.getFullYear();
  var month = currentDate.getMonth() + 1; // Adding 1 to make it 1-indexed
  var day = currentDate.getDate();
  var formattedDate = year + "-" + month + "-" + day;

  return formattedDate;
}

function getTime() {
  const currentDate = new Date();

  const hours = String(currentDate.getHours()).padStart(2, "0");
  const minutes = String(currentDate.getMinutes()).padStart(2, "0");
  const formattedTime = `${hours}:${minutes}`;

  return formattedTime;
}

//----Notification Count Badge-----
// Fetch the initial notification count when the page loads
document.addEventListener("DOMContentLoaded", function () {
  fetchNotificationCount();
});

function fetchNotificationCount() {
  // Function to fetch notification count
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "/notification_count", true);
  xhr.onreadystatechange = function () {
    if (xhr.readyState == 4 && xhr.status == 200) {
      // Update the notification badge with the fetched count
      var count = JSON.parse(xhr.responseText).count;
      var badge = document.querySelector(".notification-badge");
      if (badge && count > 0) {
        badge.textContent = count;
      }
    }
  };
  xhr.send();
}

// Event listener for the notification button
document
  .getElementById("notification-button")
  .addEventListener("click", function (event) {
    // Prevent the default behavior of the link
    event.preventDefault();

    // Remove the badge from the DOM
    var badge = document.querySelector(".notification-badge");
    if (badge) {
      badge.remove();
    }

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/reset_notification_count", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
      if (xhr.readyState == 4 && xhr.status == 200) {
        // Notification count reset successfully
        // Fetch the updated count from the server
        fetchNotificationCount();

        // Redirect to the notifications page
        window.location.href = "/notifications";
      }
    };
    xhr.send();
  });
