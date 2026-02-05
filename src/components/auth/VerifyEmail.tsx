import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { authService } from '@/api/services/authService';

const VerifyEmail = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [verificationKey, setVerificationKey] = useState(searchParams.get('key') || '');
    const [manualEntry, setManualEntry] = useState(!searchParams.get('key'));

    const { 
        mutate: verifyEmail, 
        isLoading, 
        isError, 
        error: mutationError, 
        isSuccess 
    } = useMutation({
        mutationFn: (key: string) => authService.verifyEmail(key),
        onSuccess: () => {
            // Show success state briefly before redirecting
            setTimeout(() => navigate('/login'), 2000);
        }
    });

    useEffect(() => {
        // Auto-verify if key is in URL
        if (searchParams.get('key') && !isSuccess && !isLoading) {
            verifyEmail(verificationKey);
        }
    }, [searchParams, verifyEmail, verificationKey, isSuccess, isLoading]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (verificationKey.trim()) {
            verifyEmail(verificationKey);
        }
    };

    const errorMessage = isError 
        ? (mutationError instanceof Error ? mutationError.message : 'Verification failed')
        : null;

    return (
        <div className="max-w-md mx-auto mt-10 p-6 bg-white rounded-lg shadow-md">
            <h1 className="text-2xl font-bold mb-6 text-center">Email Verification</h1>
            
            {isLoading && (
                <div className="text-center p-4">
                    <div className="animate-spin h-8 w-8 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-2"></div>
                    <p>Verifying your email...</p>
                </div>
            )}

            {isSuccess && (
                <div className="bg-green-100 p-4 rounded-md text-green-700 mb-4">
                    <p>Email verified successfully! Redirecting to login...</p>
                </div>
            )}

            {errorMessage && (
                <div className="bg-red-100 p-4 rounded-md text-red-700 mb-4">
                    <p>{errorMessage}</p>
                </div>
            )}

            {!isLoading && !isSuccess && (manualEntry || isError) && (
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Verification Key</label>
                        <input
                            type="text"
                            value={verificationKey}
                            onChange={(e) => setVerificationKey(e.target.value)}
                            className="w-full p-2 border rounded-md"
                            placeholder="Enter verification key"
                        />
                    </div>
                    <button 
                        type="submit" 
                        className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700 transition-colors"
                        disabled={isLoading}
                    >
                        Verify Email
                    </button>
                </form>
            )}
        </div>
    );
};

export default VerifyEmail;
