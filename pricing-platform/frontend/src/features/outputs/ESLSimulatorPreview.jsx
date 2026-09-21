import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

// A purely visual mock of an electronic shelf label — no real ESL
// vendor/hardware protocol involved (Phase 7 explicitly excludes that).
// Renders whatever the backend's ESL simulator adapter produced as job.payload.
export default function ESLSimulatorPreview({ payload }) {
  const isDark = payload?.theme === "dark";
  const isPortrait = payload?.orientation === "portrait";

  return (
    <Box
      sx={{
        width: isPortrait ? 160 : 260,
        height: isPortrait ? 220 : 140,
        borderRadius: 1,
        border: "3px solid #333",
        bgcolor: isDark ? "#111" : "#f5f5f0",
        color: isDark ? "#e0f7e0" : "#111",
        p: 1.5,
        fontFamily: "monospace",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      <Stack spacing={0.5}>
        <Typography variant="caption" sx={{ fontFamily: "inherit", opacity: 0.7 }} noWrap>
          {payload?.sku}
        </Typography>
        <Typography variant="body2" sx={{ fontFamily: "inherit", fontWeight: "bold" }} noWrap>
          {payload?.product_name}
        </Typography>
      </Stack>
      <Typography variant="h4" sx={{ fontFamily: "inherit", fontWeight: "bold", lineHeight: 1 }}>
        {payload?.currency} {payload?.price}
      </Typography>
      {payload?.store_name && (
        <Typography variant="caption" sx={{ fontFamily: "inherit", opacity: 0.6 }} noWrap>
          {payload.store_name}
        </Typography>
      )}
    </Box>
  );
}
