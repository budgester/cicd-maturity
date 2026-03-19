function createRadarChart(canvasId, labels, scores, previousScores) {
    var ctx = document.getElementById(canvasId).getContext('2d');
    var datasets = [
        {
            label: 'Current',
            data: scores,
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
            pointBackgroundColor: 'rgba(54, 162, 235, 1)',
        }
    ];

    if (previousScores) {
        datasets.push({
            label: 'Previous',
            data: previousScores,
            backgroundColor: 'rgba(201, 203, 207, 0.2)',
            borderColor: 'rgba(201, 203, 207, 1)',
            borderWidth: 1,
            borderDash: [5, 5],
            pointBackgroundColor: 'rgba(201, 203, 207, 1)',
        });
    }

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: datasets,
        },
        options: {
            scales: {
                r: {
                    min: 0,
                    max: 5,
                    ticks: { stepSize: 1 },
                }
            },
            plugins: {
                legend: { position: 'bottom' },
            },
        },
    });
}

function createTrendChart(canvasId, dates, overallScores, dimensionData) {
    var ctx = document.getElementById(canvasId).getContext('2d');
    var colours = [
        '#dc3545', '#fd7e14', '#ffc107', '#0d6efd', '#198754',
        '#6f42c1', '#20c997', '#0dcaf0',
    ];

    var datasets = [
        {
            label: 'Overall',
            data: overallScores,
            borderColor: '#212529',
            borderWidth: 3,
            fill: false,
            tension: 0.3,
        }
    ];

    var dimKeys = Object.keys(dimensionData);
    dimKeys.forEach(function(dim, i) {
        datasets.push({
            label: dim.replace(/_/g, ' '),
            data: dimensionData[dim],
            borderColor: colours[i % colours.length],
            borderWidth: 1,
            borderDash: [3, 3],
            fill: false,
            tension: 0.3,
            hidden: true,
        });
    });

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: datasets,
        },
        options: {
            scales: {
                y: { min: 0, max: 5, ticks: { stepSize: 1 } },
            },
            plugins: {
                legend: { position: 'bottom' },
            },
        },
    });
}
