import { memo } from 'react';

interface VerificationButtonProps {
    onClick: () => void;
    isLoading: boolean;
    disabled?: boolean;
}

const VerificationButton = memo(function VerificationButton({ 
    onClick, 
    isLoading, 
    disabled = false 
}: VerificationButtonProps) {
    return (
        <button 
            onClick={onClick} 
            disabled={isLoading || disabled} 
            className="verification-button"
        >
            {isLoading ? 'Verifying...' : 'Verify'}
        </button>
    );
});

export default VerificationButton;