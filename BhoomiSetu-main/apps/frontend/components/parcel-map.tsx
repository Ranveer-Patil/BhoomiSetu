"use client";

import "leaflet/dist/leaflet.css";
import { useEffect } from "react";
import { latLngBounds } from "leaflet";
import {
  MapContainer,
  Polygon,
  TileLayer,
  Tooltip,
  useMap,
} from "react-leaflet";
import { useT } from "@/lib/i18n";
import type { ParcelFeature } from "@/lib/types";

const colors: Record<string, string> = {
  notification: "#7c8b85",
  verification: "#3f7cac",
  objection: "#d97706",
  award: "#7c3aed",
  compensation: "#13966f",
  possession: "#185c42",
};

function FitParcels({ boundsKey }: { boundsKey: string }) {
  const map = useMap();
  useEffect(() => {
    const points = JSON.parse(boundsKey) as [number, number][];
    if (points.length)
      map.fitBounds(latLngBounds(points), { padding: [30, 30], maxZoom: 16 });
  }, [map, boundsKey]);
  return null;
}

export default function ParcelMap({
  parcels,
  onSelect,
  scrollWheelZoom = true,
}: {
  parcels: ParcelFeature[];
  onSelect?: (caseId: string) => void;
  scrollWheelZoom?: boolean;
}) {
  const t = useT();
  const boundsKey = JSON.stringify(
    parcels.flatMap((parcel) => parcel.coordinates),
  );
  return (
    <MapContainer
      center={[18.5538, 73.9505]}
      zoom={15}
      scrollWheelZoom={scrollWheelZoom}
      className="mapCanvas"
    >
      <FitParcels boundsKey={boundsKey} />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {parcels.map((parcel) => (
        <Polygon
          key={parcel.id}
          positions={parcel.coordinates}
          pathOptions={{
            color: colors[parcel.stage],
            fillColor: colors[parcel.stage],
            fillOpacity: 0.58,
            weight: 2,
          }}
          eventHandlers={{ click: () => onSelect?.(parcel.case_id) }}
        >
          <Tooltip>
            <strong>{parcel.survey_number}</strong>
            <br />
            {t(parcel.stage)} · {parcel.area_hectares.toFixed(2)} ha
          </Tooltip>
        </Polygon>
      ))}
    </MapContainer>
  );
}
