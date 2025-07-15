import React from "react";
import { useNavigate } from "react-router-dom";
import { Settings, Telescope, MapPin } from "lucide-react";
import { useTranslation } from 'react-i18next';

const ConfigDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const cards = [
    {
      title: t('config.generalConfig'),
      description: t('config.generalConfigDesc'),
      icon: <Settings className="w-8 h-8 text-blue-600" />,
      route: "/config/general",
    },
    {
      title: t('config.telescopeConfig'),
      description: t('config.telescopeConfigDesc'),
      icon: <Telescope className="w-8 h-8 text-green-600" />,
      route: "/config/telescopes",
    },
    {
      title: t('config.observatoryConfig'),
      description: t('config.observatoryConfigDesc'),
      icon: <MapPin className="w-8 h-8 text-purple-600" />,
      route: "/config/observatories",
    },
  ];

  return (
    <div className="min-h-screen flex flex-col items-center justify-top p-6 space-y-6">
      <h1 className="text-2xl font-bold mb-4">{t('config.configuration')}</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl">
        {cards.map((card) => (
          <div
            key={card.route}
            onClick={() => navigate(card.route)}
            className="cursor-pointer bg-white rounded-lg shadow hover:shadow-lg transition p-6 flex flex-col items-center text-center border border-gray-200 hover:border-blue-400"
          >
            {card.icon}
            <h2 className="text-lg font-semibold mt-2">{card.title}</h2>
            <p className="text-gray-600 mt-1">{card.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ConfigDashboard; 