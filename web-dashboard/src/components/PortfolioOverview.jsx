import { TrendingUp, TrendingDown, DollarSign, Percent } from 'lucide-react'

const PortfolioOverview = ({ data, detailed = false }) => {
  const { totalValue, dailyChange, dailyChangePercent, positions } = data

  const StatCard = ({ title, value, change, icon: Icon, prefix = '', suffix = '' }) => (
    <div className="bg-white rounded-lg p-4 border">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className="text-2xl font-bold text-gray-900">
            {prefix}{typeof value === 'number' ? value.toLocaleString() : value}{suffix}
          </p>
          {change !== undefined && (
            <div className={`flex items-center mt-1 text-sm ${
              change >= 0 ? 'text-success-600' : 'text-danger-600'
            }`}>
              {change >= 0 ? (
                <TrendingUp className="h-3 w-3 mr-1" />
              ) : (
                <TrendingDown className="h-3 w-3 mr-1" />
              )}
              {change >= 0 ? '+' : ''}{change.toFixed(2)}%
            </div>
          )}
        </div>
        <div className={`p-3 rounded-full ${
          change >= 0 ? 'bg-success-100' : change < 0 ? 'bg-danger-100' : 'bg-gray-100'
        }`}>
          <Icon className={`h-6 w-6 ${
            change >= 0 ? 'text-success-600' : change < 0 ? 'text-danger-600' : 'text-gray-600'
          }`} />
        </div>
      </div>
    </div>
  )

  if (detailed) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            title="Total Portfolio Value"
            value={totalValue}
            change={dailyChangePercent}
            icon={DollarSign}
            prefix="$"
          />
          <StatCard
            title="Daily P&L"
            value={Math.abs(dailyChange)}
            change={dailyChangePercent}
            icon={dailyChange >= 0 ? TrendingUp : TrendingDown}
            prefix={dailyChange >= 0 ? '+$' : '-$'}
          />
          <StatCard
            title="Total Positions"
            value={positions.length}
            icon={Percent}
          />
          <StatCard
            title="Available Balance"
            value={12450.75}
            icon={DollarSign}
            prefix="$"
          />
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Position Details</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-medium text-gray-600">Asset</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Amount</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Value</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">24h Change</th>
                  <th className="text-right py-3 px-4 font-medium text-gray-600">Allocation</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position, index) => {
                  const allocation = (position.value / totalValue) * 100
                  return (
                    <tr key={index} className="border-b last:border-b-0">
                      <td className="py-3 px-4">
                        <div className="font-medium">{position.symbol}</div>
                      </td>
                      <td className="text-right py-3 px-4">
                        {position.amount.toLocaleString()}
                      </td>
                      <td className="text-right py-3 px-4 font-medium">
                        ${position.value.toLocaleString()}
                      </td>
                      <td className={`text-right py-3 px-4 font-medium ${
                        position.change >= 0 ? 'text-success-600' : 'text-danger-600'
                      }`}>
                        {position.change >= 0 ? '+' : ''}{position.change.toFixed(2)}%
                      </td>
                      <td className="text-right py-3 px-4">
                        <div className="flex items-center justify-end">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div 
                              className="bg-primary-600 h-2 rounded-full" 
                              style={{ width: `${allocation}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-medium">{allocation.toFixed(1)}%</span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold">Portfolio Overview</h3>
        <div className="text-sm text-gray-600">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <StatCard
          title="Total Value"
          value={totalValue}
          change={dailyChangePercent}
          icon={DollarSign}
          prefix="$"
        />
        <StatCard
          title="Daily Change"
          value={Math.abs(dailyChange)}
          change={dailyChangePercent}
          icon={dailyChange >= 0 ? TrendingUp : TrendingDown}
          prefix={dailyChange >= 0 ? '+$' : '-$'}
        />
        <StatCard
          title="Active Positions"
          value={positions.length}
          icon={Percent}
        />
      </div>
      
      <div className="space-y-3">
        <h4 className="font-medium text-gray-900">Top Holdings</h4>
        {positions.slice(0, 3).map((position, index) => {
          const allocation = (position.value / totalValue) * 100
          return (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-xs font-bold text-primary-700">
                    {position.symbol.split('/')[0].slice(0, 2)}
                  </span>
                </div>
                <div>
                  <div className="font-medium">{position.symbol}</div>
                  <div className="text-sm text-gray-600">
                    {position.amount.toLocaleString()} units
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="font-semibold">${position.value.toLocaleString()}</div>
                <div className="flex items-center space-x-2">
                  <span className={`text-sm ${
                    position.change >= 0 ? 'text-success-600' : 'text-danger-600'
                  }`}>
                    {position.change >= 0 ? '+' : ''}{position.change.toFixed(2)}%
                  </span>
                  <span className="text-sm text-gray-600">
                    {allocation.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default PortfolioOverview