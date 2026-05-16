import Home from "./pages/Home";
import DashboardPage from "./pages/DashboardPage";
import PublicInfoPage, { publicPages, type PublicPageKey } from "./pages/PublicInfoPage";

function currentRoute() {
  const hashRoute = window.location.hash.startsWith("#/")
    ? window.location.hash.slice(1)
    : "";
  if (hashRoute) {
    return hashRoute;
  }

  const path = window.location.pathname.replace(/^\/onboard-ai/, "") || "/";
  return path.endsWith("/") && path.length > 1 ? path.slice(0, -1) : path;
}

export default function App() {
  const route = currentRoute();
  if (route === "/app" || route.startsWith("/app/")) {
    return <DashboardPage />;
  }

  const pageKey = route.replace(/^\//, "") as PublicPageKey;
  if (pageKey in publicPages) {
    return <PublicInfoPage pageKey={pageKey} />;
  }

  return <Home />;
}
