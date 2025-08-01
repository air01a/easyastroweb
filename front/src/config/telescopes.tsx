import React, { useState } from "react";
import CamerasConfig from "./cameras";
import FilterWheelsConfig from "./filterwheels";
import OpticsConfig from "./optics";
import { useTranslation } from 'react-i18next';



const ObservatoryConfig: React.FC = () => {
  const [activeTab, setActiveTab] = useState("optics");
  const { t } = useTranslation();
  const tabs = [
    { id: "optics", label: t('config.optics') },
    { id: "cameras", label: t('config.cameras') },
    { id: "filters", label: t('config.filtersWheels')},
  ];
  return (
    <div className="max-w-4xl mx-auto mt-6">
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-4" aria-label="Tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`whitespace-nowrap py-2 px-4 border-b-2 font-medium text-lg
                ${
                    activeTab === tab.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="mt-4">
        {activeTab === "optics" && <OpticsConfig />}
        {activeTab === "cameras" && <CamerasConfig />}
        {activeTab === "filters" && <FilterWheelsConfig />}
      </div>
    </div>
  );
};

export default ObservatoryConfig;
