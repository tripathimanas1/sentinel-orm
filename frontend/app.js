// Auto-detect API URL based on environment
const API_BASE = (() => {
    // Check if there's an environment variable (for Railway/Render)
    if (window.SENTINEL_API_URL) {
        return window.SENTINEL_API_URL;
    }

    // Check if running on localhost
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000/api/v1';
    }

    // For production deployments, construct API URL
    // This assumes backend is deployed at same domain with /api path
    // Adjust as needed for your deployment setup
    const protocol = window.location.protocol;
    const host = window.location.hostname;

    // Common cloud platform patterns:
    // Railway: if frontend is at sentinel-frontend.railway.app, backend is at sentinel-backend.railway.app
    // Render: if frontend is at sentinel-frontend.onrender.com, backend is at sentinel-backend.onrender.com
    if (host.includes('railway.app')) {
        // Replace 'frontend' with 'backend' in the URL
        const backendHost = host.replace('frontend', 'backend');
        return `${protocol}//${backendHost}/api/v1`;
    } else if (host.includes('onrender.com')) {
        const backendHost = host.replace('frontend', 'backend');
        return `${protocol}//${backendHost}/api/v1`;
    } else if (host.includes('netlify.app') || host.includes('vercel.app')) {
        // For separate frontend hosting, use environment variable
        // Set this in your Netlify/Vercel build settings
        return window.SENTINEL_API_URL || `${protocol}//${host}/api/v1`;
    }

    // Default: assume API is at /api/v1 on same domain
    return `${protocol}//${host}/api/v1`;
})();

console.log('Sentinel API URL:', API_BASE);

// Charts
let visibilityChartInstance = null;
let sentimentChartInstance = null;

// Initial Load
document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
});

async function loadDashboard() {
    const brandId = document.getElementById('brandInput').value;
    const container = document.getElementById('sourceCards');

    container.innerHTML = `<div class="loading-state">Accessing Sentinel Core... Fetching data for ${brandId}</div>`;

    try {
        const response = await fetch(`${API_BASE}/source-insights/${brandId}`);
        if (!response.ok) throw new Error('Failed to fetch insights');

        const data = await response.json();
        renderCards(data.platforms);
        renderCharts(data.platforms);

    } catch (error) {
        console.error(error);
        container.innerHTML = `
            <div class="glass-card" style="grid-column: 1/-1; text-align:center; color: var(--danger)">
                <h3>Connection Failure</h3>
                <p>Could not reach Sentinel Core API. Ensure backend is running on port 8000.</p>
                <p style="font-size:0.8rem; margin-top:10px; color:var(--text-muted)">${error.message}</p>
            </div>
        `;
    }
}

function renderCards(platforms) {
    const container = document.getElementById('sourceCards');
    container.innerHTML = '';

    // If no platforms, show empty state
    if (Object.keys(platforms).length === 0) {
        container.innerHTML = '<p>No platform data found.</p>';
        return;
    }

    Object.entries(platforms).forEach(([name, data]) => {
        const card = document.createElement('div');
        card.className = 'glass-card source-card';
        card.style.cursor = 'pointer';

        // Icon map
        const icons = {
            twitter: 'fa-twitter',
            reddit: 'fa-reddit-alien',
            instagram: 'fa-instagram',
            quora: 'fa-quora',
            linkedin: 'fa-linkedin'
        };
        const icon = icons[name.toLowerCase()] || 'fa-globe';

        card.innerHTML = `
            <div class="platform-header">
                <div class="platform-name"><i class="fa-brands ${icon}"></i> ${name}</div>
                <div style="color: ${data.llm_visibility.risk_level === 'High' ? 'var(--danger)' : 'var(--success)'}">
                    ${data.llm_visibility.risk_level} Risk
                </div>
            </div>
            
            <div class="metric-row">
                <span class="metric-label">Likely Views</span>
                <span class="metric-value">${data.visibility.views.toLocaleString()}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Conversions</span>
                <span class="metric-value">${data.conversions.count} ($${data.conversions.value.toFixed(2)})</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">PR Health</span>
                <span class="metric-value">${(data.pr_health.sentiment * 100).toFixed(0)}%</span>
            </div>

            <div class="llm-score">
                <span class="metric-label">LLM Visibility</span>
                <span class="score-badge">${data.llm_visibility.score.toFixed(1)}</span>
            </div>
            <div style="text-align: center; margin-top: 10px; font-size: 0.85rem; color: var(--accent);">
                <i class="fa-solid fa-circle-info"></i> Click for LLM details
            </div>
        `;

        // Add click handler to show detailed LLM breakdown
        card.addEventListener('click', () => {
            console.log('Card clicked for platform:', name);
            showLLMDetails(name, data);
        });

        container.appendChild(card);
    });
}

function showLLMDetails(platformName, data) {
    console.log('showLLMDetails called for:', platformName, data);
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';

    const crossModelScores = data.llm_visibility.cross_model_scores || {};
    const modelNames = Object.keys(crossModelScores);

    let modelsHTML = '';
    if (modelNames.length > 0) {
        modelsHTML = modelNames.map(model => `
            <div class="llm-model-row">
                <span class="model-name">${model}</span>
                <div class="model-score-bar">
                    <div class="model-score-fill" style="width: ${crossModelScores[model]}%"></div>
                    <span class="model-score-text">${crossModelScores[model].toFixed(1)}</span>
                </div>
            </div>
        `).join('');
    } else {
        modelsHTML = '<p style="color: var(--text-muted); text-align: center;">No cross-model data available</p>';
    }

    modal.innerHTML = `
        <div class="modal-content glass-card">
            <div class="modal-header">
                <h2><i class="fa-solid fa-brain"></i> LLM Visibility Details - ${platformName}</h2>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                    <i class="fa-solid fa-xmark"></i>
                </button>
            </div>
            
            <div class="modal-body">
                <div class="detail-section">
                    <h3>Overall Score</h3>
                    <div class="big-score">${data.llm_visibility.score.toFixed(1)}</div>
                    <div class="risk-badge ${data.llm_visibility.risk_level.toLowerCase()}-risk">
                        ${data.llm_visibility.risk_level} Risk
                    </div>
                </div>
                
                <div class="detail-section">
                    <h3>Per-Model Visibility Scores</h3>
                    <div class="llm-models-list">
                        ${modelsHTML}
                    </div>
                </div>
                
                <div class="detail-section">
                    <h3>Risk Analysis</h3>
                    <div class="metric-row">
                        <span class="metric-label">Risk Score</span>
                        <span class="metric-value">${data.llm_visibility.risk_score.toFixed(2)}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Potential Drop</span>
                        <span class="metric-value">${data.llm_visibility.potential_drop_pct.toFixed(1)}%</span>
                    </div>
                    ${data.llm_visibility.reasons && data.llm_visibility.reasons.length > 0 ? `
                        <div class="risk-reasons">
                            <strong>Reasons:</strong>
                            <ul>
                                ${data.llm_visibility.reasons.map(r => `<li>${r}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Close on background click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

function renderCharts(platforms) {
    const ctxVis = document.getElementById('visibilityChart').getContext('2d');
    const ctxSent = document.getElementById('sentimentChart').getContext('2d');

    const labels = Object.keys(platforms);
    const visibilityScores = labels.map(p => platforms[p].llm_visibility.score);
    const sentimentScores = labels.map(p => platforms[p].pr_health.sentiment);

    // Destroy existing
    if (visibilityChartInstance) visibilityChartInstance.destroy();
    if (sentimentChartInstance) sentimentChartInstance.destroy();

    // Visibility Chart (Radar) - Improved for clarity
    visibilityChartInstance = new Chart(ctxVis, {
        type: 'radar',
        data: {
            labels: labels.map(l => l.toUpperCase()),
            datasets: [{
                label: 'LLM Visibility Score',
                data: visibilityScores,
                backgroundColor: 'rgba(0, 243, 255, 0.25)',
                borderColor: '#00f3ff',
                borderWidth: 3,
                pointBackgroundColor: '#00f3ff',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 6,
                pointHoverRadius: 8,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#00f3ff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    min: 0,
                    max: 100,
                    ticks: {
                        stepSize: 20,
                        color: '#9494a0',
                        backdropColor: 'transparent',
                        font: {
                            size: 12,
                            weight: '500'
                        }
                    },
                    grid: {
                        color: 'rgba(255,255,255,0.15)',
                        lineWidth: 1
                    },
                    angleLines: {
                        color: 'rgba(255,255,255,0.15)',
                        lineWidth: 1
                    },
                    pointLabels: {
                        color: '#fff',
                        font: {
                            size: 13,
                            weight: '600'
                        },
                        padding: 15
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: '#fff',
                        font: {
                            size: 12
                        },
                        padding: 15
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#00f3ff',
                    bodyColor: '#fff',
                    borderColor: '#00f3ff',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function (context) {
                            return `Visibility Score: ${context.parsed.r.toFixed(1)}`;
                        }
                    }
                }
            }
        }
    });

    // Sentiment Chart (Bar)
    sentimentChartInstance = new Chart(ctxSent, {
        type: 'bar',
        data: {
            labels: labels.map(l => l.toUpperCase()),
            datasets: [{
                label: 'Sentiment',
                data: sentimentScores,
                backgroundColor: sentimentScores.map(s => s > 0 ? '#00e096' : '#ff4b4b'),
                borderRadius: 5
            }]
        },
        options: {
            scales: {
                y: {
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#9494a0' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#9494a0' }
                }
            },
            plugins: { legend: { display: false } }
        }
    });
}

async function runSimulation() {
    const brandId = document.getElementById('brandInput').value;
    const actions = Array.from(document.querySelectorAll('.checkbox-group input:checked')).map(cb => cb.value);

    const resultsContainer = document.getElementById('simResults');

    if (actions.length === 0) {
        resultsContainer.innerHTML = '<p style="color:var(--warning)">Select at least one action to simulate.</p>';
        return;
    }

    resultsContainer.innerHTML = '<p>Running Monte Carlo Simulation...</p>';

    try {
        const response = await fetch(`${API_BASE}/source-insights/simulate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                brand_id: brandId,
                actions: actions,
                model_name: "advanced-physics"
            })
        });

        if (!response.ok) throw new Error('Simulation failed');

        const data = await response.json();

        const isPositive = data.percent_change >= 0;
        const color = isPositive ? 'var(--success)' : 'var(--danger)';
        const arrow = isPositive ? '↑' : '↓';

        resultsContainer.innerHTML = `
            <div class="result-box">
                <div class="stat-label">Projected Impact</div>
                <div class="big-stat" style="background: linear-gradient(90deg, ${color}, white); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    ${arrow} ${Math.abs(data.percent_change).toFixed(2)}%
                </div>
                <p>
                    Visibility Score: <span style="color:${color}">${data.original_score.toFixed(1)}</span> 
                    → 
                    <span style="font-weight:700; color:${color}">${data.new_score.toFixed(1)}</span>
                </p>
                <div style="margin-top:15px; font-size:0.8rem; color:var(--text-muted); text-align:left; display:inline-block">
                    Volatilities Used:<br>
                    • Sentiment Sigma: ${data.volatility_used.sentiment}<br>
                    • Credibility Sigma: ${data.volatility_used.credibility}
                </div>
            </div>
        `;

    } catch (error) {
        console.error(error);
        resultsContainer.innerHTML = '<p style="color:var(--danger)">Simulation Error due to missing data.</p>';
    }
}
