// Ensures doc is ready
$(function () {
  var getData = $.get('/getChartDataNow');
  var source;
  getData.done(function (data) {
    dataRetrieved(data)
  })
  function dataRetrieved(data) {
    var config = {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [
          {
            label: "Room 1",
            backgroundColor: "rgb(255, 99, 132)",
            borderColor: "rgb(255, 99, 132)",
            borderWidth: 10,
            pointRadius: 10,
            pointHoverRadius: 10,
            data: data.data,
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        title: {
          display: true,
          text: "Real-Time Monitor",
        },
        tooltips: {
          enabled: false,
        },
        hover: {
          mode: null,
        },
        scales: {
          xAxes: [
            {
              display: true,
              scaleLabel: {
                display: true,
                labelString: "Timestamp",
              },
              ticks: {
                minRotation: 0,
                maxRotation: 0,
                autoSkip: true,
                maxTicksLimit: 10
              },
            },
          ],
          yAxes: [
            {
              display: true,
              scaleLabel: {
                display: true,
                labelString: "Power",
              },
            },
          ],
        },
      },
    };

    // This references the canvas with ID 'lineChart'
    const ctx = document.getElementById("lineChart").getContext("2d");

    // Creating a line chart using the canvas and based on the config, it configs the graph
    const lineChart = new Chart(ctx, config);

    // Server Sent Events, specify URL of page sending the updates
    source = new EventSource("/generate_chart");
    // source.onmessage is called upon update
    source.onmessage = function (event) {
      const data = JSON.parse(event.data);

      config.data.labels.shift();
      config.data.datasets[0].data.shift();

      config.data.labels.push(data.Time); // This needs to be based on JSON Name! 
      config.data.datasets[0].data.push(data.Value);
      lineChart.update();
      tableHandler();
    };
    // Shows value of datapoint when clicked
    function clickHandler(click) {
      const points = lineChart.getElementsAtEventForMode(
        click,
        "nearest",
        { intersect: true },
        true
      );
      if (points[0]) {
        const dataset = points[0]._datasetIndex;
        const index = points[0]._index;
        const label = config.data.labels[index];
        const value = config.data.datasets[dataset].data[index];
        const tr = document.querySelectorAll("tbody.click-tbody tr")[0];
        tr.children[0].innerText = label;
        tr.children[1].innerText = value;
      }
    }
    lineChart.canvas.onclick = clickHandler;

    // Creates live table
    function tableHandler() {
      if (document.getElementById("table-1")) {
        const element = document.getElementById("table-1");
        element.remove();
      }
      const chartBox = document.querySelector(".table_1");
      const tableDiv = document.createElement("DIV");
      tableDiv.setAttribute("id", "table-1");
      const table_radio = document.getElementById("table-radio");
      const both_radio = document.getElementById("both-radio");
      table_radio.checked || both_radio.checked
        ? tableDiv.setAttribute("style", "display: block")
        : tableDiv.setAttribute("style", "display: none");
      const table = document.createElement("TABLE");
      table.classList.add("table");
      const thead = table.createTHead();
      thead.classList.add("table-thead");

      var row = thead.insertRow(-1);
      var headerCell = document.createElement("th");
      headerCell.innerHTML = "Timestamp";
      row.appendChild(headerCell);
      headerCell = document.createElement("th");
      headerCell.innerHTML = "Power";
      row.appendChild(headerCell);

      const tbody = table.createTBody();
      tbody.classList.add("table-tbody");
      //Add the data rows.
      for (var i = config.data.datasets[0].data.length - 1; i > 0; i--) {
        row = tbody.insertRow(-1);
        for (var j = 0; j < 2; j++) {
          var cell = row.insertCell(-1);
          if (j == 0) {
            cell.innerHTML = config.data.labels[i];
          }
          else {
            cell.innerHTML = config.data.datasets[0].data[i];
          }
        }
      }
      chartBox.appendChild(tableDiv);
      tableDiv.appendChild(table);
    }

    // For NOW filter
    $("button#Now").on("click", function (e) {
      e.preventDefault();
      $.ajax({
        url: "/getChartDataNow",
        dataType: "text",
        // Upon getting data/response from Flask, update the graph!
        success: function (response) {
          var json = JSON.parse(response);
          lineChart.data.labels = json["labels"];
          lineChart.data.datasets[0].data = json["data"];
          lineChart.update();
        },
      });
    });

    // For 1M filter
    $("button#1M").on("click", function (e) {
      e.preventDefault();
      $.ajax({
        url: "/getChartData1M",
        dataType: "text",
        // Upon getting data/response from Flask, update the graph!
        success: function (response) {
          var json = JSON.parse(response);
          lineChart.data.labels = json["labels"];
          lineChart.data.datasets[0].data = json["data"];
          lineChart.update();
        },
      });
    });

    // For 5M filter
    $("button#5M").on("click", function (e) {
      e.preventDefault();
      $.ajax({
        url: "/getChartData5M",
        dataType: "text",
        // Upon getting data/response from Flask, update the graph!
        success: function (response) {
          var json = JSON.parse(response);
          lineChart.data.labels = json["labels"];
          lineChart.data.datasets[0].data = json["data"];
          lineChart.update();
        },
      });
    });

    // For 10M filter
    $("button#10M").on("click", function (e) {
      e.preventDefault();
      $.ajax({
        url: "/getChartData10M",
        dataType: "text",
        // Upon getting data/response from Flask, update the graph!
        success: function (response) {
          var json = JSON.parse(response);
          lineChart.data.labels = json["labels"];
          lineChart.data.datasets[0].data = json["data"];
          lineChart.update();
        },
      });
    });

    // For 30M filter
    $("button#30M").on("click", function (e) {
      e.preventDefault();
      $.ajax({
        url: "/getChartData30M'",
        dataType: "text",
        // Upon getting data/response from Flask, update the graph!
        success: function (response) {
          var json = JSON.parse(response);
          lineChart.data.labels = json["labels"];
          lineChart.data.datasets[0].data = json["data"];
          lineChart.update();
        },
      });
    });

  }
});

$(document).ajaxStart(function () {
  $("#loading").show();
});

$(document).ajaxStop(function () {
  $("#loading").hide();
});

function check_view() {
  const chart_radio = document.getElementById("chart-radio");
  const table_radio = document.getElementById("table-radio");
  const both_radio = document.getElementById("both-radio");
  const chart_box = document.getElementById("lineChart");
  const table_1 = document.getElementById("table-1");
  const table_2 = document.getElementById("table-2");
  const button_container = document.getElementsByClassName("button-container");
  chart_box.style.display =
    chart_radio.checked || both_radio.checked ? "block" : "none";
  table_1.style.display =
    table_radio.checked || both_radio.checked ? "block" : "none";
  table_2.style.display =
    chart_radio.checked || both_radio.checked ? "block" : "none";
  button_container[0].style.display =
    chart_radio.checked || both_radio.checked ? "block" : "none";
}

function changeThing() {
  var dollars_per_kwh = 0;
  dollars_per_kwh = parseFloat(document.getElementById("dollars_per_kwh").value);
  if (isNaN(parseFloat(document.getElementById("dollars_per_kwh").value))) {
    dollars_per_kwh = 0;
  } else {
    dollars_per_kwh = parseFloat(document.getElementById("dollars_per_kwh").value);
  }
  var calculated_kwh = 0
  calculated_kwh = Math.round(parseFloat(document.getElementById("calculated_kwh").innerHTML) * 100)/100;
  var bill = dollars_per_kwh * calculated_kwh * 24 * (365.24/12);
  document.getElementById("bill_calculation").innerHTML = "Your monthly bill: $" + Math.round(bill * 100)/100;
}

async function reload() {
  const response = await fetch('/reload');
  const jsonData = await response.json();
  document.getElementById("calculated_kwh").innerHTML = jsonData;
}