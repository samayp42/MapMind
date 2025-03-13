import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

// Custom label renderer
const RADIAN = Math.PI / 180;
const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index, name, value }) => {
  // Only show label for segments with more than 3% of the total
  if (percent < 0.03) return null;
  
  const radius = outerRadius * 1.2;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  // Ensure name is a string
  const nameStr = typeof name === 'object' ? JSON.stringify(name) : String(name);

  return (
    <text 
      x={x} 
      y={y} 
      fill="#333"
      textAnchor={x > cx ? 'start' : 'end'} 
      dominantBaseline="central"
      fontSize="12"
      fontWeight="500"
    >
      {`${nameStr}: ${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

const AnalysisPanel = ({ analysis }) => {
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#AF19FF', '#FF1919'];

  if (!analysis) {
    return null;
  }

  // Process pie chart data to ensure all values are primitive types
  const processedPieData = analysis.pie_chart_data?.map(item => ({
    name: typeof item.name === 'object' ? Object.keys(item.name)[0] : String(item.name),
    value: item.value
  })) || [];

  return (
    <div className="analysis-panel">
      <div className="analysis-panel-header">
        <h3>Area Analysis</h3>
      </div>
      <div className="analysis-panel-content">
        <p>{typeof analysis.summary === 'object' ? JSON.stringify(analysis.summary) : analysis.summary || "No summary available."}</p>
        
        <h4>POI Distribution</h4>
        <div className="chart-container">
          {processedPieData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={processedPieData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={30}
                  fill="#8884d8"
                  dataKey="value"
                  nameKey="name"
                  labelLine={false}
                  label={renderCustomizedLabel}
                >
                  {processedPieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value, name) => [`${value} POIs`, name]}
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e0e0e0',
                    borderRadius: '4px',
                    padding: '10px'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="no-data">No distribution data available.</p>
          )}
        </div>
        
        <h4>Market Insights</h4>
        {analysis.insights && analysis.insights.length > 0 ? (
          <ul className="insights-list">
            {analysis.insights.map((insight, index) => (
              <li key={index}>{typeof insight === 'object' ? JSON.stringify(insight) : insight}</li>
            ))}
          </ul>
        ) : (
          <p className="no-data">No insights available.</p>
        )}
        
        <h4>Recommendations</h4>
        {analysis.recommendations && analysis.recommendations.length > 0 ? (
          <ul className="recommendations-list">
            {analysis.recommendations.map((recommendation, index) => (
              <li key={index}>{typeof recommendation === 'object' ? JSON.stringify(recommendation) : recommendation}</li>
            ))}
          </ul>
        ) : (
          <p className="no-data">No recommendations available.</p>
        )}
      </div>
    </div>
  );
};

export default AnalysisPanel;