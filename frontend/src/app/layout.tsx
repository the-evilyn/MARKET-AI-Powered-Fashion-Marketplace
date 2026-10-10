import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { FavoritesProvider } from "@/context/FavoritesContext";
import Navbar from "@/components/Navbar";
import CartDrawer from "@/components/CartDrawer";
import Footer from "@/components/Footer";

export const metadata: Metadata = {
  title: "Maison — AI-Powered Fashion Marketplace",
  description: "Plateforme Haute Couture et Prêt-à-Porter de créateurs indépendants propulsée par l'intelligence artificielle.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr" className="dark">
      <body className="antialiased bg-[#070a12] text-stone-100 min-h-screen flex flex-col font-sans selection:bg-amber-400 selection:text-stone-950">
        <AuthProvider>
          <FavoritesProvider>
            <Navbar />
            <CartDrawer />
            <div className="flex-1">{children}</div>
            <Footer />
          </FavoritesProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
