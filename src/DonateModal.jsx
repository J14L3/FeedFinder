import React, { useState } from 'react';
import { X, DollarSign } from 'lucide-react';

const DonateModal = ({ post, setShowDonateModal }) => {
  const [amount, setAmount] = useState('5');
  const [customAmount, setCustomAmount] = useState('');

  const sanitizeAmount = (value) => {
    const num = Number.parseFloat(value);
    if (Number.isNaN(num)) return '';
    if (num < 1) return '1';
    if (num > 10000) return '10000';
    return num.toFixed(2);
  };

  const effectiveAmount = amount === 'custom' ? sanitizeAmount(customAmount) : sanitizeAmount(amount);
  const donateDisabled = !effectiveAmount || Number.isNaN(Number.parseFloat(effectiveAmount));

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-fadeIn" onClick={() => setShowDonateModal(null)}>
      <div className="bg-white rounded-2xl w-full max-w-md animate-slideUp" onClick={(e) => e.stopPropagation()}>
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold">Support Creator</h2>
            <button onClick={() => setShowDonateModal(null)} className="p-2 hover:bg-gray-100 rounded-full">
              <X size={24} />
            </button>
          </div>

          <div className="flex items-center gap-3 mb-6 p-4 bg-gray-50 rounded-xl">
            <img src={post.author.avatar} alt={post.author.name} className="w-12 h-12 rounded-full" />
            <div>
              <p className="font-semibold">{post.author.name}</p>
              <p className="text-sm text-gray-500">{post.author.username}</p>
            </div>
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium mb-3">Select Amount</label>
            <div className="grid grid-cols-4 gap-2 mb-3">
              {['5','10','25','50'].map(val => (
                <button key={val} onClick={() => { setAmount(val); setCustomAmount(''); }}
                  className={`py-3 rounded-lg font-semibold transition ${
                    amount === val ? 'bg-blue-500 text-white' : 'bg-gray-100 hover:bg-gray-200'
                  }`}
                >
                  ${val}
                </button>
              ))}
            </div>
            <input
              type="number"
              placeholder="Custom amount"
              min="1"
              max="10000"
              step="0.01"
              inputMode="decimal"
              value={customAmount}
              onChange={(e) => { setCustomAmount(e.target.value); setAmount('custom'); }}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
          </div>

          <button disabled={donateDisabled} className="w-full bg-blue-500 text-white font-semibold py-4 rounded-xl hover:bg-blue-600 transition flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
            <DollarSign size={20} />
            Donate ${effectiveAmount || '0.00'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DonateModal;
