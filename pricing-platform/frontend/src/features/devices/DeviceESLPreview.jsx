import BatteryFullIcon from "@mui/icons-material/BatteryFull";
import SignalCellularAltIcon from "@mui/icons-material/SignalCellularAlt";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { usePublicPrice } from "../outputs/hooks";
import { useActiveAssignment, useDeviceHealth } from "./hooks";

// The Phase 8 "React ESL simulator": visually renders what a device would
// be showing right now. There's no live MQTT-in-browser subscription (no
// MQTT broker with a websocket listener is available in this environment)
// — instead this polls the same data the backend simulator just wrote
// (device health + the public price endpoint, which reflects the fully
// rule-applied price), so it reflects a Resync within a couple of seconds.
export default function DeviceESLPreview({ device }) {
  const { data: assignment, isLoading: isAssignmentLoading } = useActiveAssignment(device.id);
  const { data: health } = useDeviceHealth(device.id, { refetchInterval: 5000 });
  const { data: priceDisplay, isLoading: isPriceLoading } = usePublicPrice(
    assignment?.product_id,
    device.store_id
  );

  const isLoading = isAssignmentLoading || (assignment && isPriceLoading);

  return (
    <Stack spacing={1} alignItems="flex-start">
      <Box
        sx={{
          width: 260,
          height: 140,
          borderRadius: 1,
          border: "3px solid #333",
          bgcolor: "#f5f5f0",
          color: "#111",
          p: 1.5,
          fontFamily: "monospace",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
        }}
      >
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="caption" sx={{ fontFamily: "inherit", opacity: 0.7 }} noWrap>
            {device.device_name}
          </Typography>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <SignalCellularAltIcon fontSize="inherit" />
            <Typography variant="caption" sx={{ fontFamily: "inherit" }}>
              {health?.signal_strength ?? "—"}%
            </Typography>
            <BatteryFullIcon fontSize="inherit" />
            <Typography variant="caption" sx={{ fontFamily: "inherit" }}>
              {health?.battery_level ?? "—"}%
            </Typography>
          </Stack>
        </Stack>

        {isLoading ? (
          <Box sx={{ display: "flex", justifyContent: "center", py: 2 }}>
            <CircularProgress size={20} />
          </Box>
        ) : !assignment ? (
          <Typography variant="body2" sx={{ fontFamily: "inherit", opacity: 0.6 }}>
            No product assigned
          </Typography>
        ) : (
          <>
            <Typography variant="body2" sx={{ fontFamily: "inherit", fontWeight: "bold" }} noWrap>
              {priceDisplay?.product_name}
            </Typography>
            <Typography variant="h4" sx={{ fontFamily: "inherit", fontWeight: "bold", lineHeight: 1 }}>
              {priceDisplay?.currency} {priceDisplay?.price}
            </Typography>
          </>
        )}

        <Typography variant="caption" sx={{ fontFamily: "inherit", opacity: 0.5 }}>
          {device.last_sync_at ? `Synced ${new Date(device.last_sync_at).toLocaleTimeString()}` : "Never synced"}
        </Typography>
      </Box>
    </Stack>
  );
}
