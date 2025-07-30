import React from 'react';
import { Outlet } from "react-router-dom";
import NavBar from '../design-system/navbar/navbar'; // adapte le chemin si besoin
import Footer from '../design-system/navbar/footer';

import { useTranslation } from 'react-i18next';
import { useObserverStore } from "../store/store"; // adapte le chemin si besoin

// On ne peut plus passer `params.locale`, donc on détecte le locale autrement (par ex. navigateur)
const RootLayout: React.FC = () => {
  const { t } = useTranslation();
  const { isConnected } = useObserverStore(); 

  const navbarItems = [
      { name: t('nav.home'), href: '/', matcher: 'exact' },
      { name: t('nav.catalog'), href: '/catalog' },
    ];

  if (isConnected) {
    navbarItems.push({ name: t('nav.plan'), href: '/plan' });
  }
  navbarItems.push({ name: t('nav.tools'), href: '/tools' });


  return (
<div className="flex flex-col min-h-screen font-sans antialiased bg-gradient-to-br from-black to-sky-800 text-white">
  <NavBar menu={navbarItems} />
  <main className="flex-1 p-4 bg-gradient-to-br from-black-950 to-sky-800 pb-16">
    <Outlet />
  </main>
  <Footer />
</div>
  );
};

export default RootLayout;
