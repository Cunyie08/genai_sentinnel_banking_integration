import React from 'react';

const RightPanel = () => {
  const transactions = [
    { name: 'MTN Airtime', amount: '-₦500' },
    { name: 'Transfer In', amount: '+₦50,000' },
    { name: 'DSTV Bill', amount: '-₦8,500' },
    { name: 'Data Bundle', amount: '-₦2,000' },
  ];

  return (
    <aside className="hidden xl:flex flex-col w-72 2xl:w-80 h-full bg-gray-50 border-l border-gray-100 shrink-0 overflow-y-auto">
      <div className="p-6 space-y-6">

        <div className="bg-white rounded-2xl p-5 shadow-sm border">
          <h4 className="text-sm font-bold text-gray-900 mb-4">
            Recent Transactions
          </h4>

          {transactions.map((tx, index) => (
            <div
              key={index}
              className="flex justify-between items-center py-2 border-b last:border-0 text-sm"
            >
              <span className="text-gray-700">{tx.name}</span>
              <span className="font-semibold">{tx.amount}</span>
            </div>
          ))}
        </div>

      </div>
    </aside>
  );
};

export default RightPanel;