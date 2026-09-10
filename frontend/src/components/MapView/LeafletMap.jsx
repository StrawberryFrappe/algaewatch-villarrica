import { useEffect, useRef } from 'react';
import { CircleMarker, MapContainer, Marker, Popup, ScaleControl, TileLayer, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import { RiskGridLayer } from './RiskGridLayer';
import { LakeMask } from './LakeMask';
import { StationCardContent } from './StationCard';
import { riskPresentation } from '../../utils/risk';

// Center/zoom/bounds match the design handoff's Mapbox spec, adapted to a
// free Leaflet + raster-tile stack (no token required):
// - Base: Esri World Imagery (satellite, free, keyless)
// - Reference overlay: Esri World Boundaries and Places (town/feature labels)
// These two together approximate the handoff's "satellite-streets" look
// without needing a Mapbox account/token.
const LAKE_CENTER = [-39.275, -72.08];
const INITIAL_ZOOM = 11.5;
const MAX_BOUNDS = [
  [-39.38, -72.28], // SW
  [-39.17, -71.90], // NE
];

// Leaflet caches its container's dimensions and only recomputes them on a
// *window* resize. Collapsing the analytics panel (380px -> 48px) resizes the
// map's container without the window changing at all, so Leaflet keeps drawing
// at the old width: a dead strip where the new area appeared, tiles that never
// load into it, and markers whose hit targets sit off from where they render.
// The <900px breakpoint that stacks the layout has the same problem.
//
// A ResizeObserver on the container is the fix. It also repairs HeatLayer's
// retry path, which waits on Leaflet's `resize` event that previously never
// fired for a container-only resize.
function AutoResize() {
  const map = useMap();

  useEffect(() => {
    if (typeof ResizeObserver === 'undefined') return undefined;
    const container = map.getContainer();
    let frame = 0;
    const observer = new ResizeObserver(() => {
      // Coalesce the burst a resize produces into one invalidate per frame.
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => map.invalidateSize());
    });
    observer.observe(container);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
    };
  }, [map]);

  return null;
}

function pulseIcon(hex) {
  return L.divIcon({
    className: '',
    html: `<span class="station-pulse-ring" style="--pulse-color:${hex}"></span>`,
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  });
}

function StationMarker({ station, hover, pinned, onEnter, onLeave, onClick, lastPassDate, projectionGap }) {
  const markerRef = useRef(null);
  const { pin } = riskPresentation(station.level);
  const isActive = hover === station.id || pinned === station.id;
  const isAlto = station.level === 'ALTO';
  const r = isActive ? 13 : 11;

  useEffect(() => {
    const marker = markerRef.current;
    if (!marker) return;
    if (isActive) marker.openPopup();
    else marker.closePopup();
  }, [isActive]);

  return (
    <>
      {isAlto && <Marker position={[station.lat, station.lng]} icon={pulseIcon(pin)} interactive={false} />}
      {/* Dark halo under the dot so it stays readable over satellite imagery. */}
      <CircleMarker
        center={[station.lat, station.lng]}
        radius={r + 2.5}
        pathOptions={{ stroke: false, fillColor: '#141F33', fillOpacity: 0.55 }}
        interactive={false}
      />
      <CircleMarker
        ref={markerRef}
        center={[station.lat, station.lng]}
        radius={r}
        pathOptions={{ color: '#FFFFFF', weight: 2.5, fillColor: pin, fillOpacity: 1 }}
        eventHandlers={{
          mouseover: () => onEnter(station.id),
          mouseout: onLeave,
          click: () => onClick(station.id),
        }}
      >
        <Tooltip direction="top" offset={[0, -10]} permanent className="station-map-label">
          {station.code} {station.name.toUpperCase()}
        </Tooltip>
        <Popup autoPan={false} closeButton={false} offset={[0, -8]} className="aw-popup">
          <StationCardContent station={station} lastPassDate={lastPassDate} projectionGap={projectionGap} />
        </Popup>
      </CircleMarker>
    </>
  );
}

export function LeafletMap({ stations, riskGrid, hover, pinned, onEnter, onLeave, onClick, lastPassDate, projectionGap }) {
  const heatPoints = riskGrid?.points ?? [];

  return (
    <MapContainer
      center={LAKE_CENTER}
      zoom={INITIAL_ZOOM}
      zoomSnap={0.1}
      minZoom={10}
      maxZoom={16}
      maxBounds={MAX_BOUNDS}
      maxBoundsViscosity={0.6}
      style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
      attributionControl={false}
    >
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        attribution="Tiles &copy; Esri"
        maxZoom={19}
      />
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
        attribution="Esri World Boundaries and Places"
        opacity={0.55}
        maxZoom={19}
      />
      <ScaleControl position="bottomright" imperial={false} />
      <AutoResize />
      <RiskGridLayer points={heatPoints} />
      <LakeMask />
      {stations.map((s) => (
        <StationMarker
          key={s.id}
          station={s}
          hover={hover}
          pinned={pinned}
          onEnter={onEnter}
          onLeave={onLeave}
          onClick={onClick}
          lastPassDate={lastPassDate}
          projectionGap={projectionGap}
        />
      ))}
    </MapContainer>
  );
}
