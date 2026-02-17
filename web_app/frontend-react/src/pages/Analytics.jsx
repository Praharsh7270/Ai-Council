import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp, DollarSign, Zap, Brain } from 'lucide-react';

const Analytics = () => {
  const navigate = useNavigate();

  // Mock data (replace with real API data)
  const stats = [
    { label: 'Total Queries', value: '0', icon: Brain, color: 'text-blue-600' },
    { label: 'Total Cost', value: '$0.00', icon: DollarSign, color: 'text-green-600' },
    { label: 'Avg Confidence', value: '0%', icon: TrendingUp, color: 'text-purple-600' },
    { label: 'Avg Time', value: '0s', icon: Zap, color: 'text-orange-600' }
  ];

  return (
    <div className="min-h-screen p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-2xl shadow-lg p-4 mb-6 flex items-center gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-6 h-6" />
          </button>
          <h1 className="text-2xl font-bold text-gray-800">Analytics</h1>
        </div>

        {/* Stats Grid */}
        <div className="grid md:grid-cols-4 gap-6 mb-6">
          {stats.map((stat, index) => (
            <div key={index} className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <stat.icon className={`w-8 h-8 ${stat.color}`} />
              </div>
              <p className="text-3xl font-bold text-gray-800 mb-1">{stat.value}</p>
              <p className="text-gray-600 text-sm">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Empty State */}
        <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
          <Brain className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-800 mb-2">No Data Yet</h3>
          <p className="text-gray-600 mb-6">
            Start chatting with AI Council to see your analytics here!
          </p>
          <button
            onClick={() => navigate('/chat')}
            className="px-6 py-3 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-lg font-semibold hover:from-primary-700 hover:to-primary-800 transition-all"
          >
            Start Chatting
          </button>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
