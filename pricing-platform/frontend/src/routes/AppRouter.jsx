import { createBrowserRouter, RouterProvider } from "react-router-dom";

import MainLayout from "../layouts/MainLayout";
import AgentCreatePage from "../pages/AgentCreatePage";
import AgentEditPage from "../pages/AgentEditPage";
import AgentRunHistoryPage from "../pages/AgentRunHistoryPage";
import AgentsListPage from "../pages/AgentsListPage";
import AIPricingDashboardPage from "../pages/AIPricingDashboardPage";
import AIPricingRecommendationDetailPage from "../pages/AIPricingRecommendationDetailPage";
import AnalyticsAIDashboardPage from "../pages/AnalyticsAIDashboardPage";
import AnalyticsDeviceDashboardPage from "../pages/AnalyticsDeviceDashboardPage";
import AnalyticsExecutiveDashboardPage from "../pages/AnalyticsExecutiveDashboardPage";
import AnalyticsInventoryDashboardPage from "../pages/AnalyticsInventoryDashboardPage";
import AnalyticsPricingDashboardPage from "../pages/AnalyticsPricingDashboardPage";
import CompetitorDetailPage from "../pages/CompetitorDetailPage";
import CompetitorPricingDashboardPage from "../pages/CompetitorPricingDashboardPage";
import CompetitorsListPage from "../pages/CompetitorsListPage";
import DashboardPage from "../pages/DashboardPage";
import DeviceCreatePage from "../pages/DeviceCreatePage";
import DeviceDetailPage from "../pages/DeviceDetailPage";
import DeviceEditPage from "../pages/DeviceEditPage";
import DevicesListPage from "../pages/DevicesListPage";
import ForgotPasswordPage from "../pages/ForgotPasswordPage";
import HomePage from "../pages/HomePage";
import ImportWizardPage from "../pages/ImportWizardPage";
import IntegrationHubCreatePage from "../pages/IntegrationHubCreatePage";
import IntegrationHubDetailPage from "../pages/IntegrationHubDetailPage";
import IntegrationHubListPage from "../pages/IntegrationHubListPage";
import IntegrationDetailPage from "../pages/IntegrationDetailPage";
import IntegrationSetupWizardPage from "../pages/IntegrationSetupWizardPage";
import IntegrationsListPage from "../pages/IntegrationsListPage";
import InventoryAdjustPage from "../pages/InventoryAdjustPage";
import InventoryDashboardPage from "../pages/InventoryDashboardPage";
import LoginPage from "../pages/LoginPage";
import NotFoundPage from "../pages/NotFoundPage";
import OutputChannelCreatePage from "../pages/OutputChannelCreatePage";
import OutputChannelEditPage from "../pages/OutputChannelEditPage";
import OutputChannelsListPage from "../pages/OutputChannelsListPage";
import OutputJobsPage from "../pages/OutputJobsPage";
import OutputRoutingRuleCreatePage from "../pages/OutputRoutingRuleCreatePage";
import OutputRoutingRuleEditPage from "../pages/OutputRoutingRuleEditPage";
import OutputRoutingRulesListPage from "../pages/OutputRoutingRulesListPage";
import PricingRuleCreatePage from "../pages/PricingRuleCreatePage";
import PricingRuleEditPage from "../pages/PricingRuleEditPage";
import PricingRuleTestPage from "../pages/PricingRuleTestPage";
import PricingRulesListPage from "../pages/PricingRulesListPage";
import PricingSimulationPage from "../pages/PricingSimulationPage";
import ProductCreatePage from "../pages/ProductCreatePage";
import ProductDetailsPage from "../pages/ProductDetailsPage";
import ProductEditPage from "../pages/ProductEditPage";
import ProductsListPage from "../pages/ProductsListPage";
import ProfilePage from "../pages/ProfilePage";
import PublicPriceDisplayPage from "../pages/PublicPriceDisplayPage";
import RegisterPage from "../pages/RegisterPage";
import RolesPermissionsPage from "../pages/RolesPermissionsPage";
import SettingsPage from "../pages/SettingsPage";
import StoreCreatePage from "../pages/StoreCreatePage";
import StoreDetailsPage from "../pages/StoreDetailsPage";
import StoreEditPage from "../pages/StoreEditPage";
import StoresListPage from "../pages/StoresListPage";
import UserCreatePage from "../pages/UserCreatePage";
import UserEditPage from "../pages/UserEditPage";
import UsersListPage from "../pages/UsersListPage";
import ProtectedRoute from "./ProtectedRoute";

const router = createBrowserRouter([
  {
    path: "/",
    element: <MainLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "login", element: <LoginPage /> },
      { path: "register", element: <RegisterPage /> },
      { path: "forgot-password", element: <ForgotPasswordPage /> },
      { path: "public/price/:productId", element: <PublicPriceDisplayPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          { path: "dashboard", element: <DashboardPage /> },
          { path: "dashboard/executive", element: <AnalyticsExecutiveDashboardPage /> },
          { path: "dashboard/pricing", element: <AnalyticsPricingDashboardPage /> },
          { path: "dashboard/inventory", element: <AnalyticsInventoryDashboardPage /> },
          { path: "dashboard/ai", element: <AnalyticsAIDashboardPage /> },
          { path: "dashboard/devices", element: <AnalyticsDeviceDashboardPage /> },
          { path: "stores", element: <StoresListPage /> },
          { path: "stores/new", element: <StoreCreatePage /> },
          { path: "stores/:storeId", element: <StoreDetailsPage /> },
          { path: "stores/:storeId/edit", element: <StoreEditPage /> },
          { path: "products", element: <ProductsListPage /> },
          { path: "products/new", element: <ProductCreatePage /> },
          { path: "products/:productId", element: <ProductDetailsPage /> },
          { path: "products/:productId/edit", element: <ProductEditPage /> },
          { path: "inventory", element: <InventoryDashboardPage /> },
          { path: "inventory/adjust", element: <InventoryAdjustPage /> },
          { path: "imports/new", element: <ImportWizardPage /> },
          { path: "pricing/rules", element: <PricingRulesListPage /> },
          { path: "pricing/rules/new", element: <PricingRuleCreatePage /> },
          { path: "pricing/rules/:ruleId/edit", element: <PricingRuleEditPage /> },
          { path: "pricing/rules/:ruleId/test", element: <PricingRuleTestPage /> },
          { path: "pricing/simulate", element: <PricingSimulationPage /> },
          { path: "competitors/dashboard", element: <CompetitorPricingDashboardPage /> },
          { path: "competitors", element: <CompetitorsListPage /> },
          { path: "competitors/:competitorId", element: <CompetitorDetailPage /> },
          { path: "ai-pricing", element: <AIPricingDashboardPage /> },
          { path: "ai-pricing/:recommendationId", element: <AIPricingRecommendationDetailPage /> },
          { path: "ai-agents", element: <AgentsListPage /> },
          { path: "ai-agents/new", element: <AgentCreatePage /> },
          { path: "ai-agents/:agentId/edit", element: <AgentEditPage /> },
          { path: "ai-agents/:agentId/runs", element: <AgentRunHistoryPage /> },
          { path: "profile", element: <ProfilePage /> },
          { path: "settings", element: <SettingsPage /> },
          { path: "users", element: <UsersListPage /> },
          { path: "users/new", element: <UserCreatePage /> },
          { path: "users/:userId/edit", element: <UserEditPage /> },
          { path: "roles", element: <RolesPermissionsPage /> },
          { path: "outputs/channels", element: <OutputChannelsListPage /> },
          { path: "outputs/channels/new", element: <OutputChannelCreatePage /> },
          { path: "outputs/channels/:channelId/edit", element: <OutputChannelEditPage /> },
          { path: "outputs/jobs", element: <OutputJobsPage /> },
          { path: "outputs/routing-rules", element: <OutputRoutingRulesListPage /> },
          { path: "outputs/routing-rules/new", element: <OutputRoutingRuleCreatePage /> },
          { path: "outputs/routing-rules/:ruleId/edit", element: <OutputRoutingRuleEditPage /> },
          { path: "devices", element: <DevicesListPage /> },
          { path: "devices/new", element: <DeviceCreatePage /> },
          { path: "devices/:deviceId", element: <DeviceDetailPage /> },
          { path: "devices/:deviceId/edit", element: <DeviceEditPage /> },
          { path: "integrations", element: <IntegrationsListPage /> },
          { path: "integrations/new", element: <IntegrationSetupWizardPage /> },
          { path: "integrations/:integrationId", element: <IntegrationDetailPage /> },
          { path: "integration-hub", element: <IntegrationHubListPage /> },
          { path: "integration-hub/new", element: <IntegrationHubCreatePage /> },
          { path: "integration-hub/:integrationId", element: <IntegrationHubDetailPage /> },
        ],
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);

export default function AppRouter() {
  return <RouterProvider router={router} />;
}
