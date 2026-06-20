import os
from jinja2 import Template
from autoeval.loader import TestSuiteResult

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoEval Report - {{ result.suite_name }}</title>
    <!-- Google Fonts Outfit & Inter -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --bg-primary: #09090b;
            --bg-secondary: #18181b;
            --bg-tertiary: #27272a;
            --border-color: #3f3f46;
            --text-primary: #fafafa;
            --text-secondary: #a1a1aa;
            --accent-purple: #a855f7;
            --accent-indigo: #6366f1;
            --accent-blue: #3b82f6;
            --success: #22c55e;
            --failure: #ef4444;
            --warning: #f59e0b;
            --font-display: 'Outfit', sans-serif;
            --font-sans: 'Inter', sans-serif;
            --shadow-premium: 0 10px 30px -10px rgba(0, 0, 0, 0.7);
            --gradient-accent: linear-gradient(135deg, var(--accent-indigo) 0%, var(--accent-purple) 100%);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            background-color: var(--bg-primary);
            color: var(--text-primary);
            font-family: var(--font-sans);
            padding: 2.5rem;
            min-height: 100vh;
        }

        h1, h2, h3, h4, .font-display {
            font-family: var(--font-display);
        }

        /* Container & Grid */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }

        /* Header Style */
        header {
            background: linear-gradient(135deg, #18181b 0%, #09090b 100%);
            border: 1px solid var(--border-color);
            border-radius: 1.25rem;
            padding: 2.5rem;
            position: relative;
            overflow: hidden;
            box-shadow: var(--shadow-premium);
        }

        header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: var(--gradient-accent);
        }

        .header-glow {
            position: absolute;
            width: 250px;
            height: 250px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
            top: -100px;
            right: -100px;
            border-radius: 50%;
            pointer-events: none;
        }

        .header-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1.5rem;
        }

        .header-info h1 {
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            background: linear-gradient(to right, #ffffff, #d8b4fe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }

        .header-meta {
            display: flex;
            gap: 1.5rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .meta-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .meta-badge {
            background: var(--bg-tertiary);
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            font-weight: 500;
        }

        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
        }

        .stat-card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: var(--shadow-premium);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            border-color: var(--accent-indigo);
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }

        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            font-family: var(--font-display);
        }

        /* Charts Row */
        .charts-row {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 1.5rem;
        }

        .chart-card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: var(--shadow-premium);
        }

        .chart-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            color: var(--text-primary);
            border-left: 3px solid var(--accent-purple);
            padding-left: 0.75rem;
        }

        .chart-container {
            position: relative;
            height: 320px;
            width: 100%;
        }

        /* Leaderboard section */
        .leaderboard-card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: var(--shadow-premium);
        }

        .table-wrapper {
            overflow-x: auto;
            margin-top: 1rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }

        th {
            background-color: var(--bg-tertiary);
            color: var(--text-secondary);
            font-family: var(--font-display);
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 1rem 1.5rem;
            border-bottom: 2px solid var(--border-color);
        }

        td {
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            font-size: 0.95rem;
        }

        tr:last-child td {
            border-bottom: none;
        }

        tr {
            transition: background-color 0.2s ease;
        }

        tr:hover td {
            background-color: rgba(255, 255, 255, 0.02);
        }

        .rank-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            font-weight: 700;
            font-family: var(--font-display);
        }

        .rank-1 {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: #000;
        }
        .rank-2 {
            background: linear-gradient(135deg, #cbd5e1 0%, #94a3b8 100%);
            color: #000;
        }
        .rank-3 {
            background: linear-gradient(135deg, #b45309 0%, #78350f 100%);
            color: #fff;
        }
        .rank-other {
            background: var(--bg-tertiary);
            color: var(--text-secondary);
        }

        .badge {
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .badge-success {
            background-color: rgba(34, 197, 94, 0.15);
            color: var(--success);
            border: 1px solid rgba(34, 197, 94, 0.3);
        }

        .badge-failure {
            background-color: rgba(239, 68, 68, 0.15);
            color: var(--failure);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        /* Inspector Section */
        .inspector-card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: var(--shadow-premium);
            display: grid;
            grid-template-columns: 320px 1fr;
            gap: 2rem;
            min-height: 500px;
        }

        @media (max-width: 900px) {
            .inspector-card {
                grid-template-columns: 1fr;
            }
        }

        .inspector-sidebar {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            border-right: 1px solid var(--border-color);
            padding-right: 1.5rem;
            max-height: 600px;
            overflow-y: auto;
        }

        @media (max-width: 900px) {
            .inspector-sidebar {
                border-right: none;
                padding-right: 0;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 1.5rem;
                max-height: 250px;
            }
        }

        .search-input {
            width: 100%;
            background-color: var(--bg-primary);
            border: 1px solid var(--border-color);
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            color: var(--text-primary);
            font-family: var(--font-sans);
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }

        .search-input:focus {
            border-color: var(--accent-indigo);
        }

        .test-list {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .test-item {
            background-color: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 0.75rem 1rem;
            cursor: pointer;
            text-align: left;
            transition: all 0.2s ease;
        }

        .test-item:hover {
            border-color: var(--accent-indigo);
            background-color: rgba(99, 102, 241, 0.05);
        }

        .test-item.active {
            border-color: var(--accent-purple);
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
            box-shadow: 0 0 15px rgba(168, 85, 247, 0.15);
        }

        .test-item-title {
            font-weight: 600;
            font-size: 0.95rem;
            margin-bottom: 0.25rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .test-item-meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        /* Detail View Area */
        .inspector-details {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            max-height: 600px;
            overflow-y: auto;
            padding-right: 0.5rem;
        }

        .model-selector {
            display: flex;
            gap: 0.75rem;
            flex-wrap: wrap;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1rem;
        }

        .model-tab {
            background-color: var(--bg-primary);
            border: 1px solid var(--border-color);
            color: var(--text-secondary);
            padding: 0.5rem 1.25rem;
            border-radius: 9999px;
            cursor: pointer;
            font-weight: 500;
            font-size: 0.85rem;
            transition: all 0.2s ease;
        }

        .model-tab:hover {
            border-color: var(--accent-blue);
            color: var(--text-primary);
        }

        .model-tab.active {
            background-color: var(--accent-indigo);
            border-color: var(--accent-indigo);
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }

        .detail-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }

        @media (max-width: 750px) {
            .detail-row {
                grid-template-columns: 1fr;
            }
        }

        .detail-block {
            background-color: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 0.75rem;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .detail-block.span-2 {
            grid-column: span 2;
        }

        @media (max-width: 750px) {
            .detail-block.span-2 {
                grid-column: span 1;
            }
        }

        .block-title {
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 0.5rem;
            margin-bottom: 0.5rem;
        }

        .block-content {
            font-size: 0.95rem;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
        }

        .eval-badge-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            margin-top: 0.5rem;
        }

        .eval-card {
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 0.5rem;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .eval-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .eval-type {
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: capitalize;
        }

        .eval-reason {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-primary);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--bg-tertiary);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--border-color);
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <div class="header-glow"></div>
            <div class="header-content">
                <div class="header-info">
                    <h1>AutoEval Run Dashboard</h1>
                    <div class="header-meta">
                        <div class="meta-item">
                            <span>Suite:</span>
                            <span class="meta-badge">{{ result.suite_name }}</span>
                        </div>
                        <div class="meta-item">
                            <span>Evaluated At:</span>
                            <span class="meta-badge">{{ result.timestamp }}</span>
                        </div>
                    </div>
                </div>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-label">Total Tests</div>
                        <div class="stat-value" style="color: var(--accent-blue);">{{ total_cases }}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Models Runs</div>
                        <div class="stat-value" style="color: var(--accent-purple);">{{ result.models_evaluated|length }}</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Overall Pass Rate</div>
                        <div class="stat-value" style="color: var(--success);">{{ overall_pass_rate }}%</div>
                    </div>
                </div>
            </div>
        </header>

        <!-- Leaderboard Table -->
        <div class="leaderboard-card">
            <h2 class="chart-title">Model Rankings</h2>
            <div class="table-wrapper">
                <table>
                    <thead>
                        <tr>
                            <th style="width: 80px;">Rank</th>
                            <th>Model Name</th>
                            <th>Avg Score</th>
                            <th>Pass Rate</th>
                            <th>Avg Latency</th>
                            <th>Total Cost</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in leaderboard %}
                        <tr>
                            <td>
                                <span class="rank-badge {% if loop.index == 1 %}rank-1{% elif loop.index == 2 %}rank-2{% elif loop.index == 3 %}rank-3{% else %}rank-other{% endif %}">
                                    {{ loop.index }}
                                </span>
                            </td>
                            <td style="font-weight: 600;">{{ row.model }}</td>
                            <td style="font-weight: 700; color: var(--accent-blue);">{{ "%.2f"|format(row.avg_score) }}</td>
                            <td>
                                <span class="badge {% if row.pass_rate >= 0.8 %}badge-success{% else %}badge-failure{% endif %}">
                                    {{ "%.1f"|format(row.pass_rate * 100) }}%
                                </span>
                            </td>
                            <td>{{ "%.2f"|format(row.avg_latency) }}s</td>
                            <td>${{ "%.6f"|format(row.total_cost) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="charts-row">
            <div class="chart-card">
                <h3 class="chart-title">Accuracy vs Latency</h3>
                <div class="chart-container">
                    <canvas id="accuracyLatencyChart"></canvas>
                </div>
            </div>
            <div class="chart-card">
                <h3 class="chart-title">Total API Cost (USD)</h3>
                <div class="chart-container">
                    <canvas id="costChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Details Inspector Section -->
        <div class="inspector-card">
            <div class="inspector-sidebar">
                <h3 class="font-display" style="font-weight: 600; margin-bottom: 0.5rem;">Test Cases</h3>
                <input type="text" class="search-input" id="testSearch" placeholder="Search tests...">
                <br>
                <div class="test-list" id="testList">
                    <!-- Dynamic populated -->
                </div>
            </div>
            <div class="inspector-details">
                <div class="model-selector" id="modelSelector">
                    <!-- Dynamic populated -->
                </div>
                
                <div class="detail-row">
                    <div class="detail-block">
                        <div class="block-title">Prompt</div>
                        <div class="block-content" id="detailPrompt">Select a test case to view prompt details.</div>
                    </div>
                    <div class="detail-block">
                        <div class="block-title">Context</div>
                        <div class="block-content" id="detailContext">-</div>
                    </div>
                </div>

                <div class="detail-block span-2">
                    <div class="block-title">Model Response Output</div>
                    <div class="block-content" id="detailOutput" style="font-family: monospace; background-color: #0c0c0e; padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border-color);">Response will load here.</div>
                </div>

                <div class="detail-row">
                    <div class="detail-block">
                        <div class="block-title">Execution Stats</div>
                        <div class="eval-badge-list">
                            <div style="display:flex; justify-content:space-between;">
                                <span style="color:var(--text-secondary)">Latency:</span>
                                <span id="statLatency" style="font-weight:600">-</span>
                            </div>
                            <div style="display:flex; justify-content:space-between;">
                                <span style="color:var(--text-secondary)">Tokens (In / Out / Total):</span>
                                <span id="statTokens" style="font-weight:600">-</span>
                            </div>
                            <div style="display:flex; justify-content:space-between;">
                                <span style="color:var(--text-secondary)">Estimated Cost:</span>
                                <span id="statCost" style="font-weight:600">-</span>
                            </div>
                        </div>
                    </div>
                    <div class="detail-block">
                        <div class="block-title">Evaluations</div>
                        <div class="eval-badge-list" id="detailEvaluations">
                            <!-- Dynamic populated -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Inject data for JS execution -->
    <script>
        const traceData = {{ raw_json_data }};
        
        let selectedTestName = "";
        let selectedModel = "";

        // Chart 1: Accuracy vs Latency
        const ctxScatter = document.getElementById('accuracyLatencyChart').getContext('2d');
        const scatterData = [];
        {% for row in leaderboard %}
        scatterData.push({
            x: {{ row.avg_latency }},
            y: {{ row.avg_score }},
            label: "{{ row.model }}"
        });
        {% endfor %}

        new Chart(ctxScatter, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Models',
                    data: scatterData,
                    backgroundColor: '#6366f1',
                    borderColor: '#a855f7',
                    pointRadius: 8,
                    pointHoverRadius: 12
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: { display: true, text: 'Average Latency (seconds)', color: '#fafafa' },
                        grid: { color: '#27272a' },
                        ticks: { color: '#a1a1aa' }
                    },
                    y: {
                        title: { display: true, text: 'Average Score (0.0 - 1.0)', color: '#fafafa' },
                        grid: { color: '#27272a' },
                        ticks: { color: '#a1a1aa' },
                        min: 0,
                        max: 1.0
                    }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                const item = ctx.raw;
                                return `${item.label}: Score=${item.y.toFixed(2)}, Latency=${item.x.toFixed(2)}s`;
                            }
                        }
                    }
                }
            }
        });

        // Chart 2: Cost Comparison
        const ctxBar = document.getElementById('costChart').getContext('2d');
        const modelNames = [];
        const costs = [];
        {% for row in leaderboard %}
        modelNames.push("{{ row.model }}");
        costs.push({{ row.total_cost }});
        {% endfor %}

        new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: modelNames,
                datasets: [{
                    label: 'Total Cost (USD)',
                    data: costs,
                    backgroundColor: 'rgba(168, 85, 247, 0.4)',
                    borderColor: '#a855f7',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#a1a1aa' }
                    },
                    y: {
                        title: { display: true, text: 'Cost (USD)', color: '#fafafa' },
                        grid: { color: '#27272a' },
                        ticks: { color: '#a1a1aa' }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });

        // Interactive Inspector Initialization
        const testListEl = document.getElementById('testList');
        const modelSelectorEl = document.getElementById('modelSelector');
        const searchInput = document.getElementById('testSearch');

        // Extract list of unique tests
        const testsMap = {};
        traceData.results.forEach(res => {
            const tName = res.test_case.name;
            if (!testsMap[tName]) {
                testsMap[tName] = {
                    test_case: res.test_case,
                    results: {}
                };
            }
            testsMap[tName].results[res.model] = res;
        });

        const testNames = Object.keys(testsMap);

        function renderTestList(filterText = "") {
            testListEl.innerHTML = "";
            let first = true;
            
            testNames.forEach(tName => {
                if (filterText && !tName.toLowerCase().includes(filterText.toLowerCase())) {
                    return;
                }
                
                const item = testsMap[tName];
                const btn = document.createElement('button');
                btn.className = `test-item ${tName === selectedTestName ? 'active' : ''}`;
                
                // Count passes
                let passes = 0;
                let total = 0;
                Object.values(item.results).forEach(r => {
                    total++;
                    const hasFail = r.evaluations.some(e => e.status === 'FAIL' || e.status === 'ERROR');
                    const hasErr = !!r.response.error;
                    if (!hasFail && !hasErr) passes++;
                });

                btn.innerHTML = `
                    <div class="test-item-title">${tName}</div>
                    <div class="test-item-meta">
                        <span>Passes: ${passes}/${total}</span>
                    </div>
                `;
                
                btn.onclick = () => selectTest(tName);
                testListEl.appendChild(btn);
                
                if (first && !selectedTestName) {
                    selectTest(tName);
                    first = false;
                }
            });
        }

        function selectTest(tName) {
            selectedTestName = tName;
            
            // Highlight test in list
            document.querySelectorAll('.test-item').forEach(el => {
                const title = el.querySelector('.test-item-title').innerText;
                if (title === tName) {
                    el.classList.add('active');
                } else {
                    el.classList.remove('active');
                }
            });
            
            const item = testsMap[tName];
            
            // Populate model tabs
            modelSelectorEl.innerHTML = "";
            const availableModels = Object.keys(item.results);
            
            if (!availableModels.includes(selectedModel)) {
                selectedModel = availableModels[0];
            }
            
            availableModels.forEach(model => {
                const tab = document.createElement('button');
                const isFail = item.results[model].evaluations.some(e => e.status === 'FAIL' || e.status === 'ERROR') || !!item.results[model].response.error;
                tab.className = `model-tab ${model === selectedModel ? 'active' : ''}`;
                tab.innerText = model;
                tab.style.borderColor = isFail ? 'rgba(239, 68, 68, 0.4)' : 'rgba(34, 197, 94, 0.4)';
                tab.onclick = () => selectModel(model);
                modelSelectorEl.appendChild(tab);
            });
            
            renderDetails();
        }

        function selectModel(model) {
            selectedModel = model;
            document.querySelectorAll('.model-tab').forEach(el => {
                if (el.innerText === model) {
                    el.classList.add('active');
                } else {
                    el.classList.remove('active');
                }
            });
            renderDetails();
        }

        function renderDetails() {
            const item = testsMap[selectedTestName];
            if (!item) return;
            
            const tc = item.test_case;
            document.getElementById('detailPrompt').innerText = tc.prompt || "";
            document.getElementById('detailContext').innerText = tc.context || "-";
            
            const res = item.results[selectedModel];
            if (!res) return;
            
            const resp = res.response;
            if (resp.error) {
                document.getElementById('detailOutput').innerText = `API ERROR:\\n${resp.error}`;
                document.getElementById('detailOutput').style.color = 'var(--failure)';
            } else {
                document.getElementById('detailOutput').innerText = resp.output || "(empty response)";
                document.getElementById('detailOutput').style.color = 'var(--text-primary)';
            }
            
            // Stats
            document.getElementById('statLatency').innerText = `${resp.latency.toFixed(2)}s`;
            document.getElementById('statTokens').innerText = `${resp.prompt_tokens} / ${resp.completion_tokens} / ${resp.total_tokens}`;
            document.getElementById('statCost').innerText = `$${resp.cost.toFixed(6)}`;
            
            // Evaluations
            const evListEl = document.getElementById('detailEvaluations');
            evListEl.innerHTML = "";
            
            if (res.evaluations && res.evaluations.length > 0) {
                res.evaluations.forEach(ev => {
                    const card = document.createElement('div');
                    card.className = "eval-card";
                    const isPass = ev.status === 'PASS';
                    
                    card.innerHTML = `
                        <div class="eval-card-header">
                            <span class="eval-type">${ev.evaluator_type}</span>
                            <span class="badge ${isPass ? 'badge-success' : 'badge-failure'}">${ev.status} (${ev.score.toFixed(2)})</span>
                        </div>
                        <div class="eval-reason">${ev.reason || ''}</div>
                    `;
                    evListEl.appendChild(card);
                });
            } else {
                evListEl.innerHTML = `<div style="color:var(--text-secondary); font-size:0.9rem;">No evaluations ran.</div>`;
            }
        }

        searchInput.oninput = (e) => {
            renderTestList(e.target.value);
        };

        // Run
        renderTestList();
    </script>
</body>
</html>
"""

class HTMLReporter:
    def write(self, result: TestSuiteResult, output_path: str):
        """Generates a beautiful HTML report from the TestSuiteResult."""
        total_cases = len(set(r.test_case.name for r in result.results))
        
        # Calculate leaderboard and statistics per model
        models = result.models_evaluated
        leaderboard_data = []
        
        total_runs = 0
        total_passed = 0
        
        for m in models:
            m_results = [r for r in result.results if r.model == m]
            
            tot_score = 0.0
            tot_latency = 0.0
            tot_cost = 0.0
            passes = 0
            
            for res in m_results:
                total_runs += 1
                tot_latency += res.response.latency
                tot_cost += res.response.cost
                
                # Check pass rate (passes if no failures and no error)
                failed = any(e.status == "FAIL" or e.status == "ERROR" for e in res.evaluations) or bool(res.response.error)
                if not failed:
                    passes += 1
                    total_passed += 1
                    
                # Score
                if res.evaluations:
                    tot_score += sum(e.score for e in res.evaluations) / len(res.evaluations)
                else:
                    tot_score += 1.0
                    
            count = len(m_results)
            avg_score = (tot_score / count) if count > 0 else 0.0
            pass_rate = (passes / count) if count > 0 else 0.0
            avg_latency = (tot_latency / count) if count > 0 else 0.0
            
            leaderboard_data.append({
                "model": m,
                "avg_score": avg_score,
                "pass_rate": pass_rate,
                "avg_latency": avg_latency,
                "total_cost": tot_cost
            })
            
        # Sort leaderboard by avg_score descending
        leaderboard_data.sort(key=lambda x: x["avg_score"], reverse=True)
        
        overall_pass_rate = int((total_passed / total_runs * 100)) if total_runs > 0 else 0
        
        # Render Jinja template
        template = Template(HTML_TEMPLATE)
        rendered_html = template.render(
            result=result,
            total_cases=total_cases,
            overall_pass_rate=overall_pass_rate,
            leaderboard=leaderboard_data,
            raw_json_data=result.model_dump_json()
        )
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(rendered_html)
