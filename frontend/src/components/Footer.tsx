import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-white border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-500">
            © 2024 TimelineNarrator v1.0.0
          </div>
          <div className="text-sm text-gray-500">
            Extract • Analyze • Narrate
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;