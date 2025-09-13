/**
 * Simple tests for StockSymbolInput component
 *
 * @description Basic functionality tests to validate TDD implementation
 */

import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'bun:test';

import { StockSymbolInput } from '../StockSymbolInput';

describe('StockSymbolInput - Basic Tests', () => {
  const mockOnAnalyze = () => {};

  it('should render without crashing', () => {
    render(<StockSymbolInput onAnalyze={mockOnAnalyze} />);
    
    // Component should render successfully
    expect(document.body).toBeTruthy();
  });

  it('should render input field', () => {
    render(<StockSymbolInput onAnalyze={mockOnAnalyze} />);
    
    const input = screen.getByRole('textbox');
    expect(input).toBeTruthy();
  });

  it('should render submit button', () => {
    render(<StockSymbolInput onAnalyze={mockOnAnalyze} />);
    
    const button = screen.getByRole('button', { name: /月次スイング分析実行/i });
    expect(button).toBeTruthy();
  });

  it('should show loading state when analyzing', () => {
    render(<StockSymbolInput onAnalyze={mockOnAnalyze} isAnalyzing={true} />);
    
    const loadingText = screen.getByText(/分析中/i);
    expect(loadingText).toBeTruthy();
  });

  it('should render popular stocks sections', () => {
    render(<StockSymbolInput onAnalyze={mockOnAnalyze} />);
    
    const usStocks = screen.getByText('米国株');
    const japanStocks = screen.getByText('日本株');
    
    expect(usStocks).toBeTruthy();
    expect(japanStocks).toBeTruthy();
  });
});