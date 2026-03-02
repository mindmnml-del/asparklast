import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";
import ContextRail from "@/components/layout/ContextRail";
import MobileTabBar from "@/components/layout/MobileTabBar";
import AuthHydrator from "@/components/providers/AuthHydrator";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthHydrator>
      <div className="flex h-screen overflow-hidden bg-background">
        <Sidebar />
        <div className="flex flex-col flex-1 md:ml-[72px]">
          <Topbar />
          <main className="flex flex-1 overflow-hidden pt-16">
            <div className="flex-1 overflow-y-auto p-6 pb-20 md:pb-6">
              {children}
            </div>
            <ContextRail />
          </main>
        </div>
        <MobileTabBar />
      </div>
    </AuthHydrator>
  );
}
