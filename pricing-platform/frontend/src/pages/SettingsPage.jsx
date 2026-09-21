import AdminPanelSettingsIcon from "@mui/icons-material/AdminPanelSettings";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import DevicesOtherIcon from "@mui/icons-material/DevicesOther";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import GroupIcon from "@mui/icons-material/Group";
import HubIcon from "@mui/icons-material/Hub";
import OutputIcon from "@mui/icons-material/Output";
import StorefrontIcon from "@mui/icons-material/Storefront";
import Box from "@mui/material/Box";
import Collapse from "@mui/material/Collapse";
import Container from "@mui/material/Container";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";

const SETTINGS_SECTIONS = [
  {
    to: "/stores",
    icon: <StorefrontIcon />,
    primary: "Store",
    secondary: "Manage the stores in your organization",
  },
  {
    key: "admin",
    icon: <AdminPanelSettingsIcon />,
    primary: "Admin",
    secondary: "Users and role/permission management for your organization",
    permission: "users.read",
    children: [
      {
        to: "/users",
        primary: "Users",
        secondary: "Create users, assign roles, and manage account status for your organization",
      },
      {
        to: "/roles",
        primary: "Roles & Permissions",
        secondary: "Reference of the system roles and the permissions each one grants",
      },
    ],
  },
  {
    key: "outputs",
    icon: <OutputIcon />,
    primary: "Outputs",
    secondary: "Output channels (ESL simulator, QR code, PDF label, web display) and job monitoring",
    children: [
      {
        to: "/outputs/channels/new",
        primary: "New Output",
        secondary: "Create a new output channel",
      },
      {
        to: "/outputs/jobs",
        primary: "Job Monitoring",
        secondary: "Track dispatched output jobs and their status",
      },
      {
        to: "/outputs/routing-rules",
        primary: "Routing Rules",
        secondary: "Automatically route price changes to output channels",
      },
    ],
  },
  {
    key: "esl-devices",
    icon: <DevicesOtherIcon />,
    primary: "ESL Devices Integration",
    secondary: "Vendor ESL integrations and the devices connected to them",
    children: [
      {
        to: "/integrations",
        primary: "Vendor Integrations",
        secondary: "Create a vendor integration with its store, then discover, import, and manage its devices",
      },
      {
        to: "/devices",
        primary: "All Devices",
        secondary: "Browse every registered device across integrations, or register one manually",
      },
    ],
  },
  {
    to: "/integration-hub",
    icon: <HubIcon />,
    primary: "Data Integrations",
    secondary: "Enterprise ERP/POS/ecommerce integrations, field mappings, and sync jobs",
  },
];

// Sections with children start expanded, except "outputs" — it's new and
// would otherwise push every later section down by default.
const DEFAULT_OPEN_KEYS = ["admin"];

export default function SettingsPage() {
  const { hasPermission } = useAuth();
  const [openKeys, setOpenKeys] = useState(DEFAULT_OPEN_KEYS);
  const toggleSection = (key) =>
    setOpenKeys((current) =>
      current.includes(key) ? current.filter((k) => k !== key) : [...current, key]
    );
  const sections = SETTINGS_SECTIONS.filter(
    (section) => !section.permission || hasPermission(section.permission)
  );

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>
      <Paper variant="outlined">
        <List disablePadding>
          {sections.map((section, index) => {
            const isLast = index === sections.length - 1;

            if (section.children) {
              const isOpen = openKeys.includes(section.key);
              return (
                <Box key={section.key}>
                  <ListItemButton
                    onClick={() => toggleSection(section.key)}
                    divider={!isOpen && !isLast}
                    sx={{ py: 2 }}
                  >
                    <ListItemIcon>{section.icon}</ListItemIcon>
                    <ListItemText primary={section.primary} secondary={section.secondary} />
                    {isOpen ? <ExpandLessIcon color="action" /> : <ExpandMoreIcon color="action" />}
                  </ListItemButton>
                  <Collapse in={isOpen} timeout="auto" unmountOnExit>
                    <List disablePadding>
                      {section.children.map((child, childIndex) => (
                        <ListItemButton
                          key={child.to}
                          component={RouterLink}
                          to={child.to}
                          divider={childIndex < section.children.length - 1 || !isLast}
                          sx={{ py: 1.5, pl: 4 }}
                        >
                          <ListItemText primary={child.primary} secondary={child.secondary} />
                          <ChevronRightIcon color="action" />
                        </ListItemButton>
                      ))}
                    </List>
                  </Collapse>
                </Box>
              );
            }

            return (
              <ListItemButton
                key={section.to}
                component={RouterLink}
                to={section.to}
                divider={!isLast}
                sx={{ py: 2 }}
              >
                <ListItemIcon>{section.icon}</ListItemIcon>
                <ListItemText primary={section.primary} secondary={section.secondary} />
                <ChevronRightIcon color="action" />
              </ListItemButton>
            );
          })}
        </List>
      </Paper>
    </Container>
  );
}
