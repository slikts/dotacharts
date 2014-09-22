/*jshint browser: true */

google.load("visualization", "1", {packages:["corechart"]});
google.setOnLoadCallback(init);

function getTicks(max, step) {
  var ticks = [];

  for (var i = step; i < Math.ceil(max / step) * step; i += step) {
    ticks.push(i);
  }

  return ticks;
}

function addChart(data, title, resolution) {
  var el = $('<div class="chart"></div>')
    .appendTo('body')[0];

  dataTable = google.visualization.arrayToDataTable(data);

  var chart = new google.visualization.LineChart(el);

  var max = 100;

  data.forEach(function(row, i) {
    if (!i) {
      return;
    }

    row.forEach(function(value, i) {
      if (!i) {
        return;
      }

      max = Math.max(max, value);
    });
  });

  var options = {
    //curveType: 'function',
    title: title,
    colors: [
      '#4a72ff',
      '#8dfdb9',
      '#b217c6',
      '#f1f100',
      '#ef7200',
      '#f08ac5',
      '#a3b42f',
      '#82d7fa',
      '#338200',
      '#9c6b00'
    ],
    vAxis: {
      ticks: [100, 200, 300, 400, 500, 600, 700],
      ticks: getTicks(max, 100)
    },
    hAxis: {
      ticks: getTicks((data.length - 2) * (resolution / 60), 2),
      minorGridlines: {
        count: 1
      }
    }
  };

  chart.draw(dataTable, options);
}

function _init(data) {
  data.charts.forEach(function(item) {
    item.data.unshift(data.top_row);
    addChart(item.data, item.name, data.resolution);
  }); 
}

function init() {
  if (typeof _data === 'undefined') {
    $.get('./' + window.location.hash.substr(1) + '.json', function(data) {
      _init(data);
    });
  } else {
    _init(_data);
  }
}