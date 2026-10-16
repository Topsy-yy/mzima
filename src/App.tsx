import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { RequireAuth } from './auth/RequireAuth';
import { Footer } from './components/layout/Footer';
import { Home } from './pages/Home';
import { Header } from './components/layout/Header';
import { HowItWorks } from './pages/HowItWorks';
import { Story } from './pages/Story';
import { SignUp } from './pages/SignUp';
import { Login } from './pages/Login';
import { Extract } from './pages/Extract';
import { ClerkLogin } from './pages/ClerkLogin';
import { NurseLogin } from './pages/NurseLogin';
import { ShiftLeadLogin } from './pages/ShiftLeadLogin';
import { ClerkDashboard } from './pages/clerk/ClerkDashboard';
import { NurseDashboard } from './pages/nurse/NurseDashboard';
import { ShiftLeadDashboard } from './pages/shiftlead/ShiftLeadDashboard';
import { NotFound } from './pages/NotFound';

function Layout({ children, signUp = false }: { children: React.ReactNode; signUp?: boolean }) {
  return (
    <>
      <Header />
      {children}
      <Footer />
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Layout><Home /></Layout>} />
          <Route path="/how-it-works" element={<Layout><HowItWorks /></Layout>} />
          <Route path="/story" element={<Layout><Story /></Layout>} />
          <Route path="/sign-up" element={<Layout signUp><SignUp /></Layout>} />
          <Route path="/login" element={<Login />} />
          <Route path="/extract" element={<RequireAuth><Extract /></RequireAuth>} />
          <Route path="/clerk-login" element={<ClerkLogin />} />
          <Route path="/nurse-login" element={<NurseLogin />} />
          <Route path="/shiftlead-login" element={<ShiftLeadLogin />} />
          <Route path="/visits" element={<RequireAuth role="clerk"><ClerkDashboard /></RequireAuth>} />
          <Route path="/triage" element={<RequireAuth role="nurse"><NurseDashboard /></RequireAuth>} />
          <Route path="/review" element={<RequireAuth role="shift_lead"><ShiftLeadDashboard /></RequireAuth>} />
          <Route path="*" element={<Layout><NotFound /></Layout>} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}