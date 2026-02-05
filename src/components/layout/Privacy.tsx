import { X } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';

interface PrivacyProps {
    open: boolean;
    onClose: () => void;
}

const Privacy: React.FC<PrivacyProps> = ({ open, onClose }) => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [isVisible, setIsVisible] = useState(open);

    useEffect(() => {
        setIsVisible(open);
    }, [open]);

    if (!isVisible) return null;

    return (
        <div className={`fixed inset-0 z-1000 overflow-y-auto bg-black bg-opacity-50 ${open ? 'animate-fade-in' : ''}`}>
            <div className="flex items-center justify-center min-h-screen p-4">
                <div 
                    ref={dialogRef}
                    className="relative w-full max-w-3xl bg-white dark:bg-gray-800 rounded-lg shadow-elevation animate-slide-up"
                >
                    <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
                        <h2 className="text-xl font-semibold font-display text-gray-900 dark:text-gray-100">Privacy Policy</h2>
                        <button 
                            onClick={onClose}
                            className="p-1.5 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                            aria-label="close"
                        >
                            <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                        </button>
                    </div>
                    
                    <div className="p-6 overflow-y-auto max-h-[70vh]">
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
                            Last Updated: April 13, 2025
                        </p>

                        <h3 className="text-lg font-semibold mt-4 mb-2">1. Introduction</h3>
                        <p className="text-gray-700 dark:text-gray-300 mb-4">
                            Welcome to Dealopia ("we," "our," or "us"). We respect your privacy and are committed to protecting your personal data. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our website and services (collectively, the "Service").
                        </p>
                        <p className="text-gray-700 dark:text-gray-300 mb-4">
                            Please read this Privacy Policy carefully. If you disagree with our policies and practices, please do not use our Service. By accessing or using Dealopia, you agree to this Privacy Policy.
                        </p>

                        <h3 className="text-lg font-semibold mt-4 mb-2">2. Data Controller</h3>
                        <p className="text-gray-700 dark:text-gray-300 mb-4">
                            Dealopia acts as a data controller for the personal data we collect through our Service. Our contact details are provided at the end of this policy.
                        </p>

                        <h3 className="text-lg font-semibold mt-4 mb-2">3. Information We Collect</h3>
                        <p className="text-gray-700 dark:text-gray-300 mb-2">
                            <strong>3.1 Personal Data</strong><br />
                            We may collect the following types of personal data:
                        </p>
                        <ul className="list-disc pl-8 mb-4 text-gray-700 dark:text-gray-300">
                            <li>Account Information: Name, email address, password, and profile information.</li>
                            <li>Contact Information: Address, phone number, and other contact details you provide.</li>
                            <li>Location Data: Geolocation information to provide location-based services.</li>
                            <li>Payment Information: Payment details when you make purchases (we process but do not store complete payment card information).</li>
                            <li>User Content: Information you provide through the Service, including reviews, comments, and user preferences.</li>
                            <li>Social Media Information: When you connect social media accounts, we may collect information from those accounts with your consent.</li>
                        </ul>

                        <p className="text-gray-700 dark:text-gray-300 mb-2">
                            <strong>3.2 Non-Personal Information</strong><br />
                            We also collect non-personal information, including:
                        </p>
                        <ul className="list-disc pl-8 mb-4 text-gray-700 dark:text-gray-300">
                            <li>Device Information: IP address, browser type, operating system, and device identifiers.</li>
                            <li>Usage Data: How you interact with our Service, including search queries, browsing history within our platform, and features you use.</li>
                            <li>Cookies and Similar Technologies: Information collected through cookies, web beacons, and similar technologies.</li>
                        </ul>

                        <h3 className="text-lg font-semibold mt-4 mb-2">4. Legal Basis for Processing</h3>
                        <p className="text-gray-700 dark:text-gray-300 mb-2">
                            We process your personal data on the following legal grounds:
                        </p>
                        <ul className="list-disc pl-8 mb-4 text-gray-700 dark:text-gray-300">
                            <li>Contract: Processing is necessary for the performance of a contract with you.</li>
                            <li>Consent: You have given clear consent for us to process your personal data for specific purposes.</li>
                            <li>Legitimate Interests: Processing is necessary for our legitimate interests, provided these interests do not override your fundamental rights and freedoms.</li>
                            <li>Legal Obligation: Processing is necessary to comply with a legal obligation.</li>
                        </ul>

                        <h3 className="text-lg font-semibold mt-4 mb-2">5. How We Use Your Information</h3>
                        <ul className="list-disc pl-8 mb-4 text-gray-700 dark:text-gray-300">
                            <li>Provide, maintain, and improve our Service</li>
                            <li>Process transactions and send related information</li>
                            <li>Personalize your experience and deliver content relevant to your interests</li>
                            <li>Notify you about changes to our Service</li>
                            <li>Communicate with you about products, services, and events</li>
                            <li>Monitor and analyze usage patterns and trends</li>
                            <li>Detect, prevent, and address technical issues and fraudulent activities</li>
                            <li>Comply with legal obligations</li>
                        </ul>

                        <h3 className="text-lg font-semibold mt-4 mb-2">15. Contact Us</h3>
                        <p className="text-gray-700 dark:text-gray-300 mb-2">
                            If you have any questions about this Privacy Policy, please contact us at:
                        </p>
                        <p className="text-gray-700 dark:text-gray-300 mb-4">
                            <strong>Data Controller:</strong> Dealopia Ltd<br />
                            <strong>Email:</strong> privacy@dealopia.com<br />
                            <strong>Address:</strong> Dealopia Headquarters, 123 Main Street, Anytown, AN 12345<br />
                            <strong>Data Protection Officer:</strong> dpo@dealopia.com
                        </p>
                    </div>
                    
                    <div className="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end">
                        <button 
                            onClick={onClose} 
                            className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
                        >
                            I Understand
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Privacy;
