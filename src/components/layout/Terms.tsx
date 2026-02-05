import React from 'react';
import { X } from 'lucide-react';

interface TermsProps {
    isOpen: boolean;
    onClose: () => void;
}

const Terms: React.FC<TermsProps> = ({ isOpen, onClose }) => {
    if (!isOpen) return null;
    
    return (
        <div className="fixed inset-0 z-9999 bg-black/50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-gray-800 w-full max-w-3xl max-h-[90vh] rounded-lg shadow-elevation overflow-hidden animate-fade-in">
                <div className="flex justify-between items-center p-4 border-b dark:border-gray-700">
                    <h2 className="text-xl font-semibold font-display">Terms of Service</h2>
                    <button 
                        onClick={onClose} 
                        className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        aria-label="close"
                    >
                        <X size={20} />
                    </button>
                </div>
                
                <div className="overflow-y-auto p-6 max-h-[70vh]">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                        Last Updated: April 13, 2025
                    </p>
                    
                    <h3 className="text-lg font-semibold mb-2">1. Introduction</h3>
                    <p className="mb-4">
                        Welcome to Dealopia. These Terms of Service ("Terms") govern your access to and use of the Dealopia website, 
                        mobile application, and other online services (collectively, the "Service"), so please read them carefully before using the Service.
                    </p>
                    <p className="mb-4">
                        By accessing or using the Service, you agree to be bound by these Terms. If you do not agree to these Terms, do not access or use the Service.
                    </p>
                    
                    <h3 className="text-lg font-semibold mb-2">2. Definitions</h3>
                    <div className="mb-4">
                        <ul className="list-disc pl-5 space-y-1">
                            <li><strong>"Dealopia"</strong> (or "we," "our," or "us") refers to Dealopia, Inc., its subsidiaries, affiliates, officers, directors, employees, agents, and contractors.</li>
                            <li><strong>"User"</strong> (or "you" or "your") refers to any individual or entity that accesses or uses the Service.</li>
                            <li><strong>"Content"</strong> refers to any information, text, graphics, photos, or other materials uploaded, downloaded, or appearing on the Service.</li>
                            <li><strong>"Deals"</strong> refers to the promotional offers, discounts, and special pricing information displayed on the Service.</li>
                        </ul>
                    </div>
                    
                    <h3 className="text-lg font-semibold mb-2">3. Account Registration and Requirements</h3>
                    <h4 className="text-base font-medium mb-1">3.1 Account Creation</h4>
                    <p className="mb-4">
                        To access certain features of the Service, you may need to register for an account. You agree to provide accurate, current, 
                        and complete information during the registration process and to update such information to keep it accurate, current, and complete.
                    </p>
                    
                    <h4 className="text-base font-medium mb-1">3.2 Account Security</h4>
                    <p className="mb-4">
                        You are responsible for safeguarding your password and for all activities that occur under your account. 
                        You agree to notify Dealopia immediately of any unauthorized use of your account or any other breach of security.
                    </p>
                    
                    <h4 className="text-base font-medium mb-1">3.3 Age Requirements</h4>
                    <p className="mb-4">
                        You must be at least 16 years old to use the Service, or the age of legal majority in your country if that is higher. 
                        By using the Service, you represent and warrant that you meet this requirement.
                    </p>
                    
                    <h3 className="text-lg font-semibold mb-2">12. GDPR Compliance</h3>
                    <p className="mb-4">
                        Dealopia complies with the General Data Protection Regulation (GDPR). We process your personal data lawfully, fairly, and in a transparent manner. 
                        You have the right to access, rectify, delete your personal data, restrict or object to processing, and data portability.
                    </p>
                    
                    <h3 className="text-lg font-semibold mb-2">13. Governing Law and Jurisdiction</h3>
                    <p className="mb-4">
                        These Terms shall be governed by and construed in accordance with the laws of the European Union and the country where you reside. 
                        Any disputes arising under these Terms will be subject to the exclusive jurisdiction of the courts located in your country of residence.
                    </p>
                    
                    <h3 className="text-lg font-semibold mb-2">14. Alternative Dispute Resolution</h3>
                    <p className="mb-4">
                        In accordance with EU regulations, you may access the European Commission's online dispute resolution platform at 
                        https://ec.europa.eu/consumers/odr to resolve any disputes related to these Terms or the Service.
                    </p>
                    
                    <h3 className="text-lg font-semibold mb-2">15. Contact Us</h3>
                    <p className="mb-4">
                        If you have any questions about these Terms, please contact us at:
                    </p>
                    <div className="mb-4">
                        <ul className="list-disc pl-5 space-y-1">
                            <li>Email: dpo@dealopia.com</li>
                            <li>Address: Dealopia EU Headquarters, 123 Main Street, Dublin, Ireland</li>
                        </ul>
                    </div>
                </div>
                
                <div className="flex justify-end p-4 border-t dark:border-gray-700">
                    <button 
                        onClick={onClose} 
                        className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-md transition-colors"
                    >
                        I Understand
                    </button>
                        </div>
                    </div>
                </div>      
            );
};

export default Terms;
