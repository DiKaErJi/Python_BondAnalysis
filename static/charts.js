function fetchAndPlotPrediction(columnName) {
    fetch(`/predict/${columnName}`)
        .then(response => response.json())
        .then(data => {
            const dates = data.map(item => item.Date.substring(0, 10)); // 只取日期部分
            const predictions = data.map(item => item[`Predicted ${columnName}`]);

            var ctx = document.getElementById('predictionChart').getContext('2d');
            var predictionChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: `Predicted ${columnName}`,
                        data: predictions,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'day'
                            }
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Error fetching prediction data:', error));
}

// 调用函数，假设我们要预测的列名是"Electricity Use (kWh)"
document.addEventListener('DOMContentLoaded', function() {
    fetchAndPlotPrediction("Electricity Use (kWh)");
    // 其他初始化函数...
});
