import React from "react";
import { useTranslation } from 'react-i18next';

type DeviceStatusProps = {
  mount_name: string;
  fw_name: string;
  focuser_name: string;
  camera_name: string;
  date: string;
  location: string;
};

const isConnected = (name: string) => name !== "Not connected";

const truncateWithTooltip = (name: string) => {
  const truncated = name.length > 40 ? name.slice(0, 40) + "..." : name;
  return (
    <span title={name} className="truncate max-w-[200px] inline-block align-middle">
      {truncated}
    </span>
  );
};

const DeviceStatus: React.FC<DeviceStatusProps> = ({
  mount_name,
  fw_name,
  focuser_name,
  camera_name,
  date,
  location,
}) => {
  const { t } = useTranslation();

  const devices = [
    { label: "mount", name: mount_name },
    { label: "camera", name: camera_name },
    { label: "focuser", name: focuser_name },
    { label: "filterwheel", name: fw_name },

  ];

  return (
    <div className="space-y-2">
      {devices.map((device, index) => (
        <div
          key={index}
          className="bg-gray-400 p-2 rounded flex justify-between items-center"
        >
          <span className="flex-1 text-gray-800">{t(devices[index].label)} : {truncateWithTooltip(device.name)}</span>
          <span className="ml-2">
            {isConnected(device.name) ? "✅" : "❌"}
          </span>
        </div>
      ))}
      <div className="bg-gray-400 p-2 rounded flex justify-between items-center">
        <span className="flex-1 text-gray-800">Date : {date}</span>
      </div>
      <div className="bg-gray-400 p-2 rounded flex justify-between items-center">
        <span className="flex-1 text-gray-800">Location : {location}</span>
      </div>
    </div>
  );
};

export default DeviceStatus;
