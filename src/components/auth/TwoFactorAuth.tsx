import { FormEvent, useCallback, useState } from 'react';
import { ArrowLeft, Loader } from 'lucide-react';
import { useVerifyTwoFactor } from '@/hooks/useAuth';

interface TwoFactorAuthProps {
  userId: string;
  onSuccess: () => void;
  onCancel: () => void;
}

interface VerificationError {
  message: string;
}

const TwoFactorAuth: React.FC<TwoFactorAuthProps> = ({
  userId,
  onSuccess,
  onCancel
}) => {
  const [token, setToken] = useState('');
  const [error, setError] = useState<string | null>(null);
  const { verifyTwoFactor, isLoading } = useVerifyTwoFactor();

  const handleTokenChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setToken(e.target.value.replace(/\D/g, '').slice(0, 6));
  }, []);

  const handleSubmit = useCallback(async (e: FormEvent) => {
    e.preventDefault();
    
    if (!token.trim()) {
      setError('Please enter the verification code');
      return;
    }
    
    try {
      setError(null);
      await verifyTwoFactor({ userId, token });
      onSuccess();
    } catch (err: unknown) {
      const error = err as VerificationError;
      setError(error.message || 'Invalid verification code');
    }
  }, [token, userId, verifyTwoFactor, onSuccess]);

  return (
    <div className="bg-neutral-900/50 backdrop-blur-sm rounded-2xl p-8 border border-neutral-800/50 max-w-md mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-display font-bold bg-gradient-to-r from-primary-200 via-white to-accent-200 bg-clip-text text-transparent mb-2">
          Two-Factor Authentication
        </h2>
        <p className="text-neutral-400">
          Enter the verification code from your authenticator app
        </p>
      </div>
      
      {error && (
        <div className="mb-6 p-4 rounded-lg bg-red-900/50 border border-red-800 text-red-200">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label 
            htmlFor="token" 
            className="block text-sm font-medium text-neutral-300 mb-1"
          >
            Verification Code
          </label>
          <input
            id="token"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            className="w-full bg-neutral-800/50 border border-neutral-700 rounded-lg px-4 py-3 text-center text-white text-xl tracking-widest focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50"
            placeholder="123456"
            value={token}
            onChange={handleTokenChange}
            maxLength={6}
            autoFocus
          />
          <p className="mt-2 text-sm text-neutral-500 text-center">
            Enter the 6-digit code from your authenticator app
          </p>
        </div>
        
        <div className="flex gap-4">
          <button
            type="button"
            onClick={onCancel}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-white transition-colors"
          >
            <ArrowLeft size={18} />
            <span>Back</span>
          </button>
          
          <button
            type="submit"
            disabled={isLoading || token.length !== 6}
            className="flex-1 bg-primary-500 hover:bg-primary-600 disabled:bg-primary-500/50 disabled:cursor-not-allowed text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader className="w-5 h-5 animate-spin" />
                <span>Verifying...</span>
              </>
            ) : (
              <span>Verify</span>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default TwoFactorAuth;
