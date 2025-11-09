import React, { useState } from 'react';
import { Crown, Check, CreditCard, Lock, Shield, Star, Sparkles, ArrowLeft } from 'lucide-react';

const PremiumUpgrade = ({ setIsPremium, setActiveTab }) => {
  const [cardNumber, setCardNumber] = useState('');
  const [cardName, setCardName] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [cvv, setCvv] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [errors, setErrors] = useState({});

  const formatCardNumber = (value) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    const matches = v.match(/\d{4,16}/g);
    const match = (matches && matches[0]) || '';
    const parts = [];
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }
    if (parts.length) {
      return parts.join(' ');
    } else {
      return v;
    }
  };

  const formatExpiryDate = (value) => {
    const v = value.replace(/\D/g, '');
    if (v.length >= 2) {
      return v.substring(0, 2) + '/' + v.substring(2, 4);
    }
    return v;
  };

  const handleCardNumberChange = (e) => {
    const formatted = formatCardNumber(e.target.value);
    setCardNumber(formatted);
  };

  const handleExpiryChange = (e) => {
    const formatted = formatExpiryDate(e.target.value);
    setExpiryDate(formatted);
  };

  const handleCvvChange = (e) => {
    const v = e.target.value.replace(/\D/g, '');
    if (v.length <= 4) {
      setCvv(v);
    }
  };

  // Luhn algorithm for card number validation
  const validateCardNumber = (cardNumber) => {
    const cleaned = cardNumber.replace(/\s/g, '');
    if (cleaned.length < 13 || cleaned.length > 19) {
      return false;
    }

    let sum = 0;
    let isEven = false;

    for (let i = cleaned.length - 1; i >= 0; i--) {
      let digit = parseInt(cleaned.charAt(i), 10);

      if (isEven) {
        digit *= 2;
        if (digit > 9) {
          digit -= 9;
        }
      }

      sum += digit;
      isEven = !isEven;
    }

    return sum % 10 === 0;
  };

  const validateExpiryDate = (expiry) => {
    if (!expiry || expiry.length !== 5) {
      return false;
    }

    const [month, year] = expiry.split('/');
    const monthNum = parseInt(month, 10);
    const yearNum = parseInt('20' + year, 10);

    if (monthNum < 1 || monthNum > 12) {
      return false;
    }

    const currentDate = new Date();
    const currentYear = currentDate.getFullYear();
    const currentMonth = currentDate.getMonth() + 1;
    const expiryDate = new Date(yearNum, monthNum - 1);

    if (yearNum < currentYear) {
      return false;
    }

    if (yearNum === currentYear && monthNum < currentMonth) {
      return false;
    }

    return true;
  };

  const validateCardName = (name) => {
    if (!name || name.trim().length < 2) {
      return false;
    }
    // Cardholder name should only contain letters, spaces, hyphens, and apostrophes
    return /^[a-zA-Z\s'-]+$/.test(name.trim());
  };

  const validateForm = () => {
    const newErrors = {};
    const cleanedCardNumber = cardNumber.replace(/\s/g, '');

    // Card number validation
    if (!cardNumber || cleanedCardNumber.length < 13) {
      newErrors.cardNumber = 'Please enter a valid card number';
    } else if (cleanedCardNumber.length > 19) {
      newErrors.cardNumber = 'Card number is too long';
    } else if (!validateCardNumber(cardNumber)) {
      newErrors.cardNumber = 'Card number is invalid';
    }

    // Cardholder name validation
    if (!cardName.trim()) {
      newErrors.cardName = 'Please enter the cardholder name';
    } else if (!validateCardName(cardName)) {
      newErrors.cardName = 'Cardholder name can only contain letters, spaces, hyphens, and apostrophes';
    } else if (cardName.trim().length > 50) {
      newErrors.cardName = 'Cardholder name is too long';
    }

    // Expiry date validation
    if (!expiryDate || expiryDate.length < 5) {
      newErrors.expiryDate = 'Please enter a valid expiry date (MM/YY)';
    } else if (!validateExpiryDate(expiryDate)) {
      newErrors.expiryDate = 'Expiry date is invalid or expired';
    }

    // CVV validation
    if (!cvv || cvv.length < 3) {
      newErrors.cvv = 'Please enter a valid CVV';
    } else if (cvv.length > 4) {
      newErrors.cvv = 'CVV must be 3 or 4 digits';
    } else if (!/^\d+$/.test(cvv)) {
      newErrors.cvv = 'CVV must contain only numbers';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});
    
    if (!validateForm()) {
      return;
    }

    setIsProcessing(true);

    // Simulate payment processing
    setTimeout(() => {
      setIsProcessing(false);
      setShowSuccess(true);
      
      // Upgrade user to premium after 2 seconds
      setTimeout(() => {
        setIsPremium(true);
        setActiveTab('home');
      }, 2000);
    }, 2000);
  };

  const premiumFeatures = [
    { icon: Star, text: 'Unlimited ratings on posts' },
    { icon: Sparkles, text: 'Access to exclusive content' },
    { icon: Crown, text: 'Premium badge on your profile' }
  ];

  if (showSuccess) {
    return (
      <div className="w-full">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 md:p-8">
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Check size={40} className="text-green-600" />
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Welcome to Premium!</h2>
            <p className="text-gray-600 mb-8">Your payment was successful. You now have access to all premium features.</p>
            <div className="flex items-center justify-center gap-2 text-yellow-600 mb-6">
              <Crown size={24} />
              <span className="text-lg font-semibold">Premium Member</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 md:p-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => setActiveTab('home')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition"
          >
            <ArrowLeft size={20} />
            <span>Back</span>
          </button>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-xl flex items-center justify-center">
              <Crown size={28} className="text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Upgrade to Premium</h1>
          </div>
          <p className="text-gray-600">Unlock unlimited ratings and exclusive content</p>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Left Column - Features */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Premium Benefits</h2>
            <div className="space-y-4 mb-6">
              {premiumFeatures.map((feature, index) => {
                const Icon = feature.icon;
                return (
                  <div key={index} className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Icon size={18} className="text-blue-600" />
                    </div>
                    <p className="text-gray-700">{feature.text}</p>
                  </div>
                );
              })}
            </div>

            {/* Pricing */}
            <div className="bg-gradient-to-br from-yellow-50 to-orange-50 rounded-xl p-6 border border-yellow-200">
              <div className="flex items-baseline gap-2 mb-2">
                <span className="text-4xl font-bold text-gray-900">$9.99</span>
                <span className="text-gray-600">/month</span>
              </div>
              <p className="text-sm text-gray-600 mb-4">Cancel anytime. No hidden fees.</p>
              <div className="flex items-center gap-2 text-green-600">
                <Shield size={18} />
                <span className="text-sm font-medium">Secure payment processing</span>
              </div>
            </div>
          </div>

          {/* Right Column - Payment Form */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Payment Information</h2>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Card Number */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Card Number
                </label>
                <div className="relative">
                  <CreditCard size={20} className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="text"
                    value={cardNumber}
                    onChange={(e) => {
                      handleCardNumberChange(e);
                      if (errors.cardNumber) {
                        setErrors({ ...errors, cardNumber: '' });
                      }
                    }}
                    onBlur={validateForm}
                    placeholder="1234 5678 9012 3456"
                    maxLength={19}
                    className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none ${
                      errors.cardNumber ? 'border-red-500' : 'border-gray-300'
                    }`}
                    required
                  />
                </div>
                {errors.cardNumber && (
                  <p className="text-red-500 text-sm mt-1">{errors.cardNumber}</p>
                )}
              </div>

              {/* Cardholder Name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cardholder Name
                </label>
                <input
                  type="text"
                  value={cardName}
                  onChange={(e) => {
                    setCardName(e.target.value);
                    if (errors.cardName) {
                      setErrors({ ...errors, cardName: '' });
                    }
                  }}
                  onBlur={validateForm}
                  placeholder="John Doe"
                  className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none ${
                    errors.cardName ? 'border-red-500' : 'border-gray-300'
                  }`}
                  required
                  maxLength={50}
                />
              </div>
              {errors.cardName && (
                <p className="text-red-500 text-sm mt-1">{errors.cardName}</p>
              )}

              {/* Expiry and CVV */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Expiry Date
                  </label>
                  <input
                    type="text"
                    value={expiryDate}
                    onChange={(e) => {
                      handleExpiryChange(e);
                      if (errors.expiryDate) {
                        setErrors({ ...errors, expiryDate: '' });
                      }
                    }}
                    onBlur={validateForm}
                    placeholder="MM/YY"
                    maxLength={5}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none ${
                      errors.expiryDate ? 'border-red-500' : 'border-gray-300'
                    }`}
                    required
                  />
                  {errors.expiryDate && (
                    <p className="text-red-500 text-sm mt-1">{errors.expiryDate}</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    CVV
                  </label>
                  <input
                    type="text"
                    value={cvv}
                    onChange={(e) => {
                      handleCvvChange(e);
                      if (errors.cvv) {
                        setErrors({ ...errors, cvv: '' });
                      }
                    }}
                    onBlur={validateForm}
                    placeholder="123"
                    maxLength={4}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none ${
                      errors.cvv ? 'border-red-500' : 'border-gray-300'
                    }`}
                    required
                  />
                  {errors.cvv && (
                    <p className="text-red-500 text-sm mt-1">{errors.cvv}</p>
                  )}
                </div>
              </div>

              {/* Security Notice */}
              <div className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg">
                <Lock size={18} className="text-gray-600 flex-shrink-0 mt-0.5" />
                <p className="text-xs text-gray-600">
                  Your payment information is encrypted and secure. We use industry-standard SSL encryption to protect your data.
                </p>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isProcessing}
                className="w-full bg-gradient-to-r from-yellow-400 to-orange-500 text-white font-semibold py-4 rounded-xl hover:from-yellow-500 hover:to-orange-600 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg"
              >
                {isProcessing ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Processing...
                  </>
                ) : (
                  <>
                    <Crown size={20} />
                    Upgrade to Premium - $9.99/month
                  </>
                )}
              </button>

              <p className="text-xs text-center text-gray-500">
                By upgrading, you agree to our Terms of Service and Privacy Policy
              </p>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PremiumUpgrade;
