const ctx = document.getElementById('predictionChart');

if (ctx) {

    new Chart(ctx, {

        type: 'line',

        data: {

            labels: ['Yesterday', 'Today', 'Tomorrow'],

            datasets: [

                {

                    label: 'ICU LOS Trend',

                    data: [4, 7, 6],

                    borderWidth: 3,

                    tension: 0.4

                },

                {

                    label: 'Mortality Risk',

                    data: [20, 45, 35],

                    borderWidth: 3,

                    tension: 0.4

                }

            ]
        },

        options: {

            responsive: true,

            plugins: {

                legend: {

                    labels: {

                        font: {

                            size: 14

                        }

                    }

                }

            },

            scales: {

                y: {

                    beginAtZero: true

                }

            }

        }

    });

}