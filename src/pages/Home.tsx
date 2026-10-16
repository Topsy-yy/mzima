import { useNavigate } from 'react-router-dom';
import React from 'react';
import { Hero } from '../sections/Hero';
import { ProblemStrip } from '../sections/ProblemStrip';
import { SolutionRows } from '../sections/SolutionRows';
import { RolesStrip } from '../sections/RolesStrip';
import { SafetyBlock } from '../sections/SafetyBlock';
import { ComparisonTable } from '../sections/ComparisonTable';
import { Faq } from '../sections/Faq';
import { ClosingCta } from '../sections/ClosingCta';

export function Home() {
  const navigate = useNavigate();
  return (
    <main id="main">
      <Hero onNavigate={navigate} />
      <ProblemStrip />
      <SolutionRows />
      <RolesStrip />
      <SafetyBlock />
      <ComparisonTable />
      <Faq />
      <ClosingCta onNavigate={navigate} />
    </main>
  );
}