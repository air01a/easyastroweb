import React from "react";

type DeviceStatusProps = {
  mount_name: string;
  fw_name: string;
  focuser_name: string;
  camera_name: string;
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
}) => {
  const devices = [
    { label: "Mount", name: mount_name },
    { label: "Camera", name: camera_name },
    { label: "Focuser", name: focuser_name },
    { label: "Wheel", name: fw_name },

  ];

  return (
    <div className="space-y-2">
      {devices.map((device, index) => (
        <div
          key={index}
          className="bg-gray-400 p-2 rounded flex justify-between items-center"
        >
          <span className="flex-1 text-gray-800">{devices[index].label} : {truncateWithTooltip(device.name)}</span>
          <span className="ml-2">
            {isConnected(device.name) ? "✅" : "❌"}
          </span>
        </div>
      ))}
    </div>
  );
};

export default DeviceStatus;
