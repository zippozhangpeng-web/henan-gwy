/**
 * ECharts 图表配置 — 好风公考情报站 · 高区分度配色
 */

// 高区分度色板（暖色系内但差异明显）
const COLORS = {
  // 主序列 — 彩虹暖色递进
  seq: ['#FF6B35', '#FFB347', '#00B894', '#6C5CE7', '#FF3366', '#00CEC9', '#FDCB6E', '#A29BFE'],
  // 进面分专用 — 直观语义
  scoreLow: '#00B894',    // 绿 = 低分友好
  scoreAvg: '#FFB347',    // 黄橙 = 中等
  scoreHigh: '#FF3366',   // 玫红 = 高分竞争
  // 渐变辅助
  gradient: function(c1, c2) {
    return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
      { offset: 0, color: c1 },
      { offset: 1, color: c2 }
    ]);
  }
};

// ========== 首页统计图表 ==========

function initCitiesBarChart(elementId, data) {
    const chart = echarts.init(document.getElementById(elementId));
    chart.setOption({
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'shadow' },
            backgroundColor: '#fff',
            borderColor: '#E8E8F0',
            borderWidth: 2,
            textStyle: { color: '#333' }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
            type: 'category',
            data: data.map(d => d.city),
            axisLabel: { rotate: 45, fontSize: 11, color: '#636E72' },
            axisLine: { lineStyle: { color: '#E8E8F0' } }
        },
        yAxis: { 
            type: 'value', name: '岗位数',
            nameTextStyle: { color: '#636E72' },
            axisLine: { show: false },
            splitLine: { lineStyle: { color: '#F0F0F5', type: 'dashed' } }
        },
        series: [{
            type: 'bar',
            data: data.map((d, i) => ({
                value: d.cnt,
                itemStyle: { color: COLORS.seq[i % COLORS.seq.length] }
            })),
            barWidth: '60%',
            itemStyle: { borderRadius: [6, 6, 0, 0] },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0,0,0,0.15)'
                }
            }
        }]
    });
    return chart;
}

function initYearTrendChart(elementId, data) {
    const chart = echarts.init(document.getElementById(elementId));
    chart.setOption({
        tooltip: { 
            trigger: 'axis',
            backgroundColor: '#fff',
            borderColor: '#E8E8F0',
            borderWidth: 2,
            textStyle: { color: '#333' }
        },
        legend: { 
            data: ['岗位数', '招录人数'],
            textStyle: { color: '#636E72' }
        },
        xAxis: {
            type: 'category',
            data: data.map(d => d.year + '年'),
            axisLabel: { color: '#636E72', fontWeight: 600 },
            axisLine: { lineStyle: { color: '#E8E8F0' } }
        },
        yAxis: [
            { 
                type: 'value', name: '岗位数',
                nameTextStyle: { color: '#636E72' },
                axisLine: { show: false },
                splitLine: { lineStyle: { color: '#F0F0F5', type: 'dashed' } }
            },
            { 
                type: 'value', name: '招录人数',
                nameTextStyle: { color: '#636E72' },
                axisLine: { show: false },
                splitLine: { show: false }
            }
        ],
        series: [
            {
                name: '岗位数',
                type: 'bar',
                data: data.map(d => d.cnt),
                itemStyle: {
                    borderRadius: [6, 6, 0, 0],
                    color: COLORS.gradient('#FF8C5A', '#FF6B35')
                },
                barWidth: '40%'
            },
            {
                name: '招录人数',
                type: 'line',
                yAxisIndex: 1,
                data: data.map(d => d.total_recruit),
                lineStyle: { color: '#6C5CE7', width: 3 },
                itemStyle: { color: '#6C5CE7' },
                symbol: 'diamond',
                symbolSize: 10,
                areaStyle: {
                    color: COLORS.gradient('rgba(108,92,231,0.15)', 'rgba(108,92,231,0.02)')
                }
            }
        ]
    });
    return chart;
}

// 高区分度饼图色板（视觉差异明显）
const PIE_COLORS = [
  '#FF6B35', '#6C5CE7', '#00B894', '#FFB347', '#FF3366',
  '#00CEC9', '#FDCB6E', '#A29BFE', '#E55D2B', '#74B9FF'
];

function initSystemPieChart(elementId, data) {
    const chart = echarts.init(document.getElementById(elementId));
    chart.setOption({
        tooltip: { 
            trigger: 'item', 
            formatter: '{b}: {c} ({d}%)',
            backgroundColor: '#fff',
            borderColor: '#E8E8F0',
            borderWidth: 2
        },
        legend: {
            type: 'scroll',
            orient: 'vertical',
            right: 10,
            top: 20,
            bottom: 20,
            textStyle: { color: '#636E72' }
        },
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['40%', '50%'],
            avoidLabelOverlap: false,
            itemStyle: {
                borderRadius: 6,
                borderColor: '#fff',
                borderWidth: 2
            },
            label: { show: false },
            emphasis: {
                label: { show: true, fontSize: 14, fontWeight: 'bold' }
            },
            data: data.map((d, i) => ({ 
                name: d.system_type, 
                value: d.cnt,
                itemStyle: { color: PIE_COLORS[i % PIE_COLORS.length] }
            }))
        }]
    });
    return chart;
}

function initEduPieChart(elementId, data) {
    const chart = echarts.init(document.getElementById(elementId));
    chart.setOption({
        tooltip: { 
            trigger: 'item', 
            formatter: '{b}: {c} ({d}%)',
            backgroundColor: '#fff',
            borderColor: '#E8E8F0',
            borderWidth: 2
        },
        series: [{
            type: 'pie',
            radius: ['0%', '70%'],
            center: ['50%', '50%'],
            data: data.map((d, i) => ({
                name: d.education,
                value: d.cnt,
                itemStyle: { color: PIE_COLORS[i % PIE_COLORS.length] }
            })),
            label: {
                formatter: '{b}\n{d}%',
                color: '#636E72'
            },
            emphasis: {
                itemStyle: { 
                    shadowBlur: 10, 
                    shadowOffsetX: 0, 
                    shadowColor: 'rgba(0,0,0,0.2)' 
                }
            }
        }]
    });
    return chart;
}

// ========== 岗位详情页 - 四维雷达图 ==========

function initRadarChart(elementId, scores) {
    const chart = echarts.init(document.getElementById(elementId));
    chart.setOption({
        radar: {
            center: ['50%', '55%'],
            radius: '70%',
            indicator: [
                { name: '🎯 上岸难度', max: 10 },
                { name: '📍 地区优劣', max: 10 },
                { name: '💰 薪酬待遇', max: 10 },
                { name: '📈 发展前景', max: 10 }
            ],
            axisName: {
                color: '#2D3436',
                fontSize: 13,
                fontWeight: 700
            },
            shape: 'polygon',
            splitArea: {
                areaStyle: {
                    color: ['rgba(108,92,231,0.03)', 'rgba(108,92,231,0.05)',
                            'rgba(108,92,231,0.07)', 'rgba(108,92,231,0.1)']
                }
            },
            splitLine: {
                lineStyle: { color: 'rgba(108,92,231,0.15)' }
            },
            axisLine: {
                lineStyle: { color: 'rgba(108,92,231,0.2)' }
            }
        },
        series: [{
            type: 'radar',
            data: [{
                value: [
                    scores.difficulty_score,
                    scores.region_score,
                    scores.salary_score,
                    scores.prospect_score
                ],
                name: '岗位评分',
                areaStyle: {
                    color: COLORS.gradient('rgba(255,107,53,0.3)', 'rgba(108,92,231,0.05)')
                },
                lineStyle: { color: '#FF6B35', width: 2.5 },
                itemStyle: { color: '#6C5CE7' },
                symbol: 'circle',
                symbolSize: 7
            }]
        }]
    });
    return chart;
}

// ========== 迷你雷达图（首页推荐卡片用）==========

function initMiniRadarChart(elementId, scores) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const chart = echarts.init(el);
    chart.setOption({
        radar: {
            center: ['50%', '55%'],
            radius: '65%',
            indicator: [
                { name: '上岸难度', max: 10 },
                { name: '地区优劣', max: 10 },
                { name: '薪酬待遇', max: 10 },
                { name: '发展前景', max: 10 }
            ],
            axisName: {
                color: '#636E72',
                fontSize: 9,
                fontWeight: 600
            },
            shape: 'polygon',
            splitArea: {
                areaStyle: {
                    color: ['rgba(108,92,231,0.02)', 'rgba(108,92,231,0.04)',
                            'rgba(108,92,231,0.06)', 'rgba(108,92,231,0.08)']
                }
            },
            splitLine: {
                lineStyle: { color: 'rgba(108,92,231,0.1)' }
            },
            axisLine: {
                lineStyle: { color: 'rgba(108,92,231,0.15)' }
            },
            splitNumber: 4
        },
        series: [{
            type: 'radar',
            symbol: 'none',
            data: [{
                value: [
                    scores.difficulty_score,
                    scores.region_score,
                    scores.salary_score,
                    scores.prospect_score
                ],
                areaStyle: {
                    color: COLORS.gradient('rgba(255,107,53,0.25)', 'rgba(108,92,231,0.04)')
                },
                lineStyle: { color: '#FF6B35', width: 1.8 },
                itemStyle: { color: '#FF6B35' }
            }]
        }]
    });
    return chart;
}

// ========== 分数线柱状图（语义化配色）==========

function initScoreBar(elementId, minScore, maxScore, avgScore) {
    const chart = echarts.init(document.getElementById(elementId));
    chart.setOption({
        tooltip: { 
            trigger: 'axis',
            backgroundColor: '#fff',
            borderColor: '#E8E8F0',
            borderWidth: 2,
            formatter: function(params) {
                var colors = ['#00B894', '#FFB347', '#FF3366'];
                return params.map(function(p, i) {
                    return '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:' + colors[i] + ';margin-right:5px;"></span>' 
                        + p.name + ': <strong>' + p.value.toFixed(2) + '</strong>';
                }).join('<br/>');
            }
        },
        xAxis: {
            type: 'category',
            data: ['最低进面分', '平均进面分', '最高进面分'],
            axisLabel: { color: '#636E72', fontWeight: 600 },
            axisLine: { lineStyle: { color: '#E8E8F0' } }
        },
        yAxis: {
            type: 'value',
            name: '分数',
            min: 40,
            max: 90,
            nameTextStyle: { color: '#636E72' },
            splitLine: { lineStyle: { color: '#F0F0F5', type: 'dashed' } }
        },
        series: [{
            type: 'bar',
            data: [
                { 
                    value: minScore, 
                    itemStyle: { 
                        color: COLORS.gradient('#55EFC4', '#00B894'),
                        borderRadius: [8, 8, 0, 0]
                    }
                },
                { 
                    value: avgScore, 
                    itemStyle: { 
                        color: COLORS.gradient('#FFD93D', '#FFB347'),
                        borderRadius: [8, 8, 0, 0]
                    }
                },
                { 
                    value: maxScore, 
                    itemStyle: { 
                        color: COLORS.gradient('#FF8C5A', '#FF3366'),
                        borderRadius: [8, 8, 0, 0]
                    }
                }
            ],
            barWidth: '50%',
            label: { 
                show: true, 
                position: 'top', 
                fontWeight: 'bold',
                color: '#2D3436',
                fontSize: 14,
                formatter: function(p) { return p.value.toFixed(2); }
            }
        }]
    });
    return chart;
}

// ========== 单柱图（仅估算分）==========

function initScoreBarSingle(elementId, minScore) {
    const chart = echarts.init(document.getElementById(elementId));
    chart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: ['参考进面分'], axisLabel: { color: '#636E72', fontWeight: 600 } },
        yAxis: { type: 'value', name: '分数', min: 40, max: 90, splitLine: { lineStyle: { type: 'dashed' } } },
        series: [{
            type: 'bar',
            data: [{ value: minScore, itemStyle: { color: '#FFB347', borderRadius: [8,8,0,0] } }],
            barWidth: '40%',
            label: { show: true, position: 'top', fontWeight: 'bold', fontSize: 14, formatter: function(p) { return p.value.toFixed(2); } }
        }]
    });
    chart.setOption({
        graphic: [{
            type: 'text',
            left: 'center',
            top: 10,
            style: { text: '⚠️ 参考数据（基于2025年同维度均值估算）', fill: '#999', fontSize: 11 }
        }]
    });
    return chart;
}

// ========== 全局分析页 - 分数分布 ==========

function initScoreDistribution(elementId, data) {
    const chart = echarts.init(document.getElementById(elementId));
    chart.setOption({
        tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' },
            backgroundColor: '#fff',
            borderColor: '#E8E8F0',
            borderWidth: 2
        },
        xAxis: {
            type: 'category',
            data: data.buckets,
            name: '分数段',
            axisLabel: { color: '#636E72' },
            axisLine: { lineStyle: { color: '#E8E8F0' } }
        },
        yAxis: { 
            type: 'value', name: '岗位数',
            nameTextStyle: { color: '#636E72' },
            splitLine: { lineStyle: { color: '#F0F0F5', type: 'dashed' } }
        },
        series: [{
            type: 'bar',
            data: data.counts.map((v, i) => ({
                value: v,
                itemStyle: { 
                    color: COLORS.seq[i % COLORS.seq.length],
                    borderRadius: [6, 6, 0, 0]
                }
            })),
            barWidth: '60%',
            emphasis: {
                itemStyle: {
                    shadowBlur: 8,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0,0,0,0.15)'
                }
            }
        }]
    });
    return chart;
}

function initCityScoreChart(elementId, data) {
    const chart = echarts.init(document.getElementById(elementId));
    chart.setOption({
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#fff',
            borderColor: '#E8E8F0',
            borderWidth: 2,
            formatter: function(params) {
                var result = '<strong>' + params[0].axisValue + '</strong><br/>';
                params.forEach(function(p) {
                    var val = p.seriesName === '平均进面分' ? p.value.toFixed(2) : p.value;
                    result += p.marker + ' ' + p.seriesName + ': <strong>' + val + '</strong><br/>';
                });
                return result;
            }
        },
        legend: { 
            data: ['平均进面分', '岗位数'],
            textStyle: { color: '#636E72' }
        },
        xAxis: {
            type: 'category',
            data: data.map(d => d.city),
            axisLabel: { rotate: 45, color: '#636E72' },
            axisLine: { lineStyle: { color: '#E8E8F0' } }
        },
        yAxis: [
            { 
                type: 'value', name: '分数',
                nameTextStyle: { color: '#636E72' },
                splitLine: { lineStyle: { color: '#F0F0F5', type: 'dashed' } }
            },
            { 
                type: 'value', name: '岗位数',
                nameTextStyle: { color: '#636E72' },
                splitLine: { show: false }
            }
        ],
        series: [
            {
                name: '平均进面分',
                type: 'bar',
                data: data.map(d => d.avg_score),
                itemStyle: { 
                    color: COLORS.gradient('#FF8C5A', '#FF6B35'),
                    borderRadius: [6, 6, 0, 0] 
                },
                barWidth: '50%'
            },
            {
                name: '岗位数',
                type: 'line',
                yAxisIndex: 1,
                data: data.map(d => d.cnt),
                lineStyle: { color: '#6C5CE7', width: 2.5 },
                itemStyle: { color: '#6C5CE7' },
                symbol: 'diamond',
                symbolSize: 8,
                areaStyle: {
                    color: COLORS.gradient('rgba(108,92,231,0.12)', 'rgba(108,92,231,0.01)')
                }
            }
        ]
    });
    return chart;
}

// 响应式处理
window.addEventListener('resize', function() {
    document.querySelectorAll('[id^="chart-"]').forEach(function(el) {
        const instance = echarts.getInstanceByDom(el);
        if (instance) instance.resize();
    });
});

// ========== 历史分数波动折线图 ==========

function initVolatilityChart(elementId, data) {
    // data: [{year, min_score, max_score, avg_score, is_estimated}...]
    const el = document.getElementById(elementId);
    if (!el || !data || data.length < 2) return;

    const chart = echarts.init(el);

    const years = data.map(function(d) { return d.year + '年'; });

    // 真实数据和估算数据分别处理
    const realData = data.map(function(d) {
        return d.is_estimated ? null : {
            value: d.avg_score || d.min_score,
            year: d.year,
            min: d.min_score,
            max: d.max_score,
            avg: d.avg_score
        };
    });
    const estimatedData = data.map(function(d) {
        return d.is_estimated ? {
            value: d.avg_score || d.min_score,
            year: d.year,
            min: d.min_score,
            max: d.max_score,
            avg: d.avg_score
        } : null;
    });

    // Compute the full series (connecting line through all points)
    const fullSeries = data.map(function(d) {
        return d.avg_score || d.min_score;
    });

    chart.setOption({
        tooltip: {
            trigger: 'axis',
            backgroundColor: '#fff',
            borderColor: '#E8E8F0',
            borderWidth: 2,
            textStyle: { color: '#333', fontSize: 13 },
            formatter: function(params) {
                var result = '<strong>' + params[0].axisValue + '</strong><br/>';
                params.forEach(function(p) {
                    if (p.value !== undefined && p.value !== null) {
                        var marker = p.seriesName.indexOf('参考') >= 0
                            ? '<span style="display:inline-block;width:8px;height:8px;border:2px dashed #FFB347;border-radius:50%;margin-right:6px;"></span>'
                            : '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#6C5CE7;margin-right:6px;"></span>';
                        var d = data[p.dataIndex];
                        var lines = [];
                        lines.push(marker + ' 进面分: <strong>' + p.value.toFixed(2) + '</strong>');
                        if (d.min_score) lines.push('&nbsp;&nbsp;&nbsp;最低: ' + d.min_score.toFixed(2));
                        if (d.max_score) lines.push('&nbsp;&nbsp;&nbsp;最高: ' + d.max_score.toFixed(2));
                        if (d.avg_score) lines.push('&nbsp;&nbsp;&nbsp;平均: ' + d.avg_score.toFixed(2));
                        if (d.is_estimated) lines.push('&nbsp;&nbsp;&nbsp;<span style=\"color:#E17055\">⚠️ 参考分</span>');
                        return lines.join('<br/>');
                    }
                    return '';
                }).filter(function(s) { return s.length > 0; }).join('<br/>');
            }
        },
        grid: {
            left: '8%',
            right: '5%',
            top: '10%',
            bottom: '10%'
        },
        xAxis: {
            type: 'category',
            data: years,
            boundaryGap: false,
            axisLabel: {
                color: '#636E72',
                fontWeight: 600,
                fontSize: 12
            },
            axisLine: { lineStyle: { color: '#E8E8F0' } },
            axisTick: { alignWithLabel: true }
        },
        yAxis: {
            type: 'value',
            name: '进面分数',
            nameTextStyle: { color: '#636E72', fontSize: 12 },
            axisLabel: { color: '#636E72' },
            splitLine: { lineStyle: { color: '#F0F0F5', type: 'dashed' } },
            min: function(value) { return Math.floor(value.min - 3); },
            max: function(value) { return Math.ceil(value.max + 3); }
        },
        series: [
            {
                name: '进面分',
                type: 'line',
                data: fullSeries,
                smooth: 0.3,
                lineStyle: { color: '#6C5CE7', width: 2.5 },
                symbol: 'circle',
                symbolSize: function(value, params) {
                    if (data[params.dataIndex].is_estimated) return 8;
                    return 10;
                },
                itemStyle: {
                    color: function(params) {
                        if (data[params.dataIndex].is_estimated) return '#fff';
                        return '#6C5CE7';
                    },
                    borderColor: function(params) {
                        if (data[params.dataIndex].is_estimated) return '#FFB347';
                        return '#6C5CE7';
                    },
                    borderWidth: function(params) {
                        if (data[params.dataIndex].is_estimated) return 2.5;
                        return 0;
                    }
                },
                markLine: {
                    silent: true,
                    symbol: 'none',
                    lineStyle: { color: 'rgba(108,92,231,0.2)', type: 'dashed', width: 1 },
                    data: [{
                        type: 'average',
                        name: '均值',
                        label: {
                            formatter: '均值 {c}',
                            color: '#636E72',
                            fontSize: 11
                        }
                    }]
                },
                areaStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                        { offset: 0, color: 'rgba(108,92,231,0.12)' },
                        { offset: 1, color: 'rgba(108,92,231,0.01)' }
                    ])
                },
                z: 2
            }
        ]
    });

    return chart;
}
