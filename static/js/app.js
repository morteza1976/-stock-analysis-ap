/**
 * Main JavaScript file for Stock Analysis Platform
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });
    
    // Handle stock chart rendering
    const candlestickChart = document.getElementById('candlestick-chart');
    if (candlestickChart) {
        const chartData = JSON.parse(candlestickChart.getAttribute('data-chart'));
        renderCandlestickChart(chartData, candlestickChart);
    }
    
    // Trend score visualization
    const trendScoreBars = document.querySelectorAll('.trend-score-bar');
    trendScoreBars.forEach(bar => {
        const scoreValue = parseFloat(bar.getAttribute('data-score')) || 0;
        const normalizedScore = Math.min(Math.max(scoreValue, 0), 100); // Clamp between 0-100
        const indicator = bar.querySelector('.trend-score-indicator');
        if (indicator) {
            indicator.style.width = `${normalizedScore}%`;
        }
    });
});

/**
 * Render a candlestick chart using Plotly.js
 * 
 * @param {Object} chartData - Historical price data for the stock
 * @param {HTMLElement} container - Container element for the chart
 */
function renderCandlestickChart(chartData, container) {
    if (!chartData || !chartData.dates || !chartData.dates.length) {
        container.innerHTML = '<div class="alert alert-warning">No chart data available</div>';
        return;
    }
    
    // Create candlestick trace
    const trace = {
        x: chartData.dates,
        open: chartData.open,
        high: chartData.high,
        low: chartData.low,
        close: chartData.close,
        type: 'candlestick',
        name: 'Price',
        increasing: {line: {color: '#4CAF50'}},
        decreasing: {line: {color: '#F44336'}}
    };
    
    // Add volume as bar chart if available
    let data = [trace];
    if (chartData.volume && chartData.volume.length) {
        const volumeTrace = {
            x: chartData.dates,
            y: chartData.volume,
            type: 'bar',
            name: 'Volume',
            yaxis: 'y2',
            marker: {
                color: 'rgba(100, 100, 255, 0.3)'
            }
        };
        data.push(volumeTrace);
    }
    
    // Add support and resistance lines if available
    if (chartData.supportResistance) {
        const sr = chartData.supportResistance;
        
        if (sr.support1) {
            data.push({
                x: chartData.dates,
                y: Array(chartData.dates.length).fill(sr.support1),
                type: 'scatter',
                mode: 'lines',
                name: 'Support 1',
                line: {
                    color: 'rgba(76, 175, 80, 0.7)',
                    width: 2,
                    dash: 'dot'
                }
            });
        }
        
        if (sr.resistance1) {
            data.push({
                x: chartData.dates,
                y: Array(chartData.dates.length).fill(sr.resistance1),
                type: 'scatter',
                mode: 'lines',
                name: 'Resistance 1',
                line: {
                    color: 'rgba(244, 67, 54, 0.7)',
                    width: 2,
                    dash: 'dot'
                }
            });
        }
        
        // Add moving averages
        if (sr.ma20 && chartData.ma20) {
            data.push({
                x: chartData.dates,
                y: chartData.ma20,
                type: 'scatter',
                mode: 'lines',
                name: '20-day MA',
                line: {
                    color: 'rgba(66, 133, 244, 0.8)',
                    width: 2
                }
            });
        }
        
        if (sr.ma50 && chartData.ma50) {
            data.push({
                x: chartData.dates,
                y: chartData.ma50,
                type: 'scatter',
                mode: 'lines',
                name: '50-day MA',
                line: {
                    color: 'rgba(255, 152, 0, 0.8)',
                    width: 2
                }
            });
        }
    }
    
    // Define layout
    const layout = {
        title: `${chartData.ticker} Stock Price`,
        dragmode: 'zoom',
        margin: {
            r: 10,
            t: 40,
            b: 40,
            l: 60
        },
        showlegend: true,
        xaxis: {
            rangeslider: {
                visible: false
            },
            type: 'date',
            title: 'Date'
        },
        yaxis: {
            title: 'Price',
            autorange: true,
            domain: [0.3, 1]
        },
        yaxis2: {
            title: 'Volume',
            autorange: true,
            domain: [0, 0.2]
        },
        shapes: []
    };
    
    // Add earnings dates as vertical lines if available
    if (chartData.earningsDates && chartData.earningsDates.length) {
        chartData.earningsDates.forEach(date => {
            layout.shapes.push({
                type: 'line',
                xref: 'x',
                yref: 'paper',
                x0: date,
                y0: 0,
                x1: date,
                y1: 1,
                line: {
                    color: 'purple',
                    width: 1,
                    dash: 'dash'
                }
            });
        });
    }
    
    // Render chart
    Plotly.newPlot(container, data, layout);
}

/**
 * Format a number as currency
 * 
 * @param {number} value - The value to format
 * @param {string} currency - Currency code (default: USD)
 * @returns {string} Formatted currency string
 */
function formatCurrency(value, currency = 'USD') {
    if (value === null || value === undefined) return '';
    
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

/**
 * Format a large number with abbreviations (K, M, B, T)
 * 
 * @param {number} value - The value to format
 * @returns {string} Formatted number string
 */
function formatLargeNumber(value) {
    if (value === null || value === undefined) return '';
    
    if (value >= 1e12) {
        return (value / 1e12).toFixed(2) + 'T';
    } else if (value >= 1e9) {
        return (value / 1e9).toFixed(2) + 'B';
    } else if (value >= 1e6) {
        return (value / 1e6).toFixed(2) + 'M';
    } else if (value >= 1e3) {
        return (value / 1e3).toFixed(2) + 'K';
    } else {
        return value.toString();
    }
} 