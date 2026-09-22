import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

/**
 * A simple live preview of the PDF shelf label, driven by the
 * template's colors. It mirrors the backend's three-column layout
 * (text / unit-price box / QR zone) and the banner, so the user can
 * see exactly how their color choices affect the rendered label —
 * no PDF generation needed for this preview, so it's instant and works
 * on mobile.
 *
 * This is a *mockup preview only* (same fidelity as ESLSimulatorPreview):
 * the real PDF is generated server-side. The goal is to show color impact
 * in real time, not pixel-perfect parity with the reportlab renderer.
 */
export default function LabelPreview({ colors }) {
  const labelW = 240;
  const labelH = 150;
  const pad = 6;      // Scaled from 2mm (2 * 3)
  const gap = 4.5;    // Scaled from 1.5mm (1.5 * 3)
  const bannerH = 13.5; // Scaled from 4.5mm (4.5 * 3)
  const unitBoxW = 50;

  const bannerColor = colors.banner ?? "#111111";
  const textColor = colors.text ?? "#111111";
  const borderColor = colors.border ?? "#111111";
  const unitBorderColor = colors.unit_border ?? "#111111";
  const sublabelColor = colors.sublabel ?? "#666666";
  const placeholderColor = colors.placeholder ?? "#AAAAAA";
  const bgColor = colors.background ?? "#FFFFFF";

  const priceText = "$49.99";
  const productName = "Wireless Mouse";
  const unitPriceText = "$4.99";

  return (
    <Box
      sx={{
        width: "100%",
        maxWidth: 260,
        aspectRatio: `${labelW}/${labelH}`,
        border: "1px solid #ccc",
        borderRadius: 1,
        overflow: "hidden",
        bgcolor: bgColor,
      }}
    >
      <svg
        width={labelW}
        height={labelH}
        viewBox={`0 0 ${labelW} ${labelH}`}
        xmlns="http://www.w3.org/2000/svg"
        style={{ width: "100%", height: "100%" }}
      >
        {/* Background */}
        <rect x={0} y={0} width={labelW} height={labelH} fill={bgColor} />

        {/* Outer border */}
        <rect
          x={pad}
          y={pad}
          width={labelW - pad * 2}
          height={labelH - pad * 2}
          rx={2}
          ry={2}
          fill="none"
          stroke={borderColor}
          strokeWidth={2}
        />

        {/* Bottom banner */}
        <rect
          x={pad}
          y={labelH - pad - bannerH}
          width={labelW - pad * 2}
          height={bannerH}
          fill={bannerColor}
        />
        <text
          x={labelW / 2}
          y={labelH - pad - bannerH / 2 + 4}
          textAnchor="middle"
          fill="#FFFFFF"
          fontSize={11}
          fontWeight="bold"
          fontFamily="Helvetica, Arial, sans-serif"
        >
          Store Name
        </text>

        {/* Unit price box (center column) */}
        <g transform={`translate(${labelW - pad - unitBoxW}, ${pad + 10})`}>
          <rect
            x={0}
            y={0}
            width={unitBoxW}
            height={50}
            rx={3}
            ry={3}
            fill="none"
            stroke={unitBorderColor}
            strokeWidth={1}
          />
          <text
            x={unitBoxW / 2}
            y={13}
            textAnchor="middle"
            fill={textColor}
            fontSize={7}
            fontWeight="bold"
            fontFamily="Helvetica, Arial, sans-serif"
          >
            UNIT PRICE
          </text>
          <text
            x={unitBoxW / 2}
            y={32}
            textAnchor="middle"
            fill={textColor}
            fontSize={12}
            fontWeight="bold"
            fontFamily="Helvetica, Arial, sans-serif"
          >
            {unitPriceText}
          </text>
          <text
            x={unitBoxW / 2}
            y={44}
            textAnchor="middle"
            fill={sublabelColor}
            fontSize={6}
            fontFamily="Helvetica, Arial, sans-serif"
          >
            PER EA
          </text>
        </g>

        {/* Text zone */}
        <g transform={`translate(${pad + 6}, ${pad + 6})`}>
          <text
            x={0}
            y={0}
            fill={textColor}
            fontSize={10}
            fontWeight="bold"
            fontFamily="Helvetica, Arial, sans-serif"
          >
            {productName}
          </text>
          <text
            x={0}
            y={15}
            fill={sublabelColor}
            fontSize={6.5}
            fontFamily="Helvetica, Arial, sans-serif"
          >
            RETAIL PRICE
          </text>
          <text
            x={0}
            y={30}
            fill={textColor}
            fontSize={20}
            fontWeight="bold"
            fontFamily="Helvetica, Arial, sans-serif"
          >
            {priceText}
          </text>
          <text
            x={0}
            y={42}
            fill={placeholderColor}
            fontSize={6}
            fontFamily="Helvetica, Arial, sans-serif"
          >
            SKU-000
          </text>
        </g>

        {/* QR zone placeholder */}
        <g transform={`translate(${labelW - pad - unitBoxW - 14}, ${pad + 10})`}>
          <rect
            x={0}
            y={0}
            width={40}
            height={50}
            fill="none"
            stroke={placeholderColor}
            strokeWidth={1}
            strokeDasharray="3,2"
          />
          <text
            x={20}
            y={48}
            textAnchor="middle"
            fill={placeholderColor}
            fontSize={5}
            fontFamily="Helvetica, Arial, sans-serif"
          >
            QR
          </text>
        </g>
      </svg>
    </Box>
  );
}
