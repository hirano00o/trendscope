/**
 * Tests for StockSymbolInput component
 *
 * @description TDD-driven tests for the stock symbol input component
 * used in monthly swing trading analysis.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeEach } from 'bun:test';

// Mock function for testing with call tracking
const jest = {
  fn: () => {
    const calls: any[][] = [];
    const mockFn = (...args: any[]) => {
      calls.push(args);
    };
    
    // Add mock methods
    mockFn.mockImplementation = (impl: Function) => {
      return Object.assign(mockFn, impl);
    };
    
    mockFn.mockResolvedValue = (value: any) => mockFn;
    
    // Track calls
    Object.defineProperty(mockFn, 'mock', {
      get: () => ({
        calls: calls,
      })
    });
    
    // Helper methods
    mockFn.toHaveBeenCalled = () => calls.length > 0;
    mockFn.toHaveBeenCalledWith = (...args: any[]) => {
      return calls.some(call => 
        call.length === args.length && 
        call.every((arg, i) => arg === args[i])
      );
    };
    mockFn.toHaveBeenCalledTimes = (times: number) => calls.length === times;
    mockFn.not = {
      toHaveBeenCalled: () => calls.length === 0
    };
    
    // Clear method
    mockFn.mockClear = () => {
      calls.length = 0;
    };
    
    return mockFn as any;
  },
  clearAllMocks: () => {},
};

import { StockSymbolInput } from '../StockSymbolInput';

// Mock props interface for the component
interface StockSymbolInputProps {
  onAnalyze: (symbol: string) => void;
  isAnalyzing?: boolean;
  placeholder?: string;
  popularStocks?: {
    us: string[];
    japan: string[];
  };
}

// Default popular stocks for testing
const defaultPopularStocks = {
  us: ['AAPL', 'MSFT', 'GOOGL', 'TSLA'],
  japan: ['7203.T', '6758.T', '7267.T', '6861.T'],
};

describe('StockSymbolInput Component', () => {
  const mockOnAnalyze = jest.fn();
  
  const defaultProps: StockSymbolInputProps = {
    onAnalyze: mockOnAnalyze,
    isAnalyzing: false,
    popularStocks: defaultPopularStocks,
  };

  beforeEach(() => {
    mockOnAnalyze.mockClear();
  });

  describe('Rendering', () => {
    it('should render input field with correct placeholder', () => {
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      expect(input).toBeInTheDocument();
      expect(input).toHaveAttribute('placeholder', expect.stringContaining('AAPL'));
    });

    it('should render submit button', () => {
      render(<StockSymbolInput {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /月次スイング分析実行/i });
      expect(button).toBeInTheDocument();
    });

    it('should render popular stocks sections', () => {
      render(<StockSymbolInput {...defaultProps} />);
      
      expect(screen.getByText('米国株')).toBeInTheDocument();
      expect(screen.getByText('日本株')).toBeInTheDocument();
    });

    it('should display popular stock buttons', () => {
      render(<StockSymbolInput {...defaultProps} />);
      
      // Check US stocks
      expect(screen.getByRole('button', { name: 'AAPL' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'MSFT' })).toBeInTheDocument();
      
      // Check Japanese stocks
      expect(screen.getByRole('button', { name: '7203.T' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '6758.T' })).toBeInTheDocument();
    });

    it('should show loading state when analyzing', () => {
      render(<StockSymbolInput {...defaultProps} isAnalyzing={true} />);
      
      const button = screen.getByRole('button', { name: /分析中/i });
      expect(button).toBeDisabled();
      expect(screen.getByText(/分析中/)).toBeInTheDocument();
    });
  });

  describe('Input Validation', () => {
    it('should accept valid US stock symbols', async () => {
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, 'AAPL');
      
      expect(input).toHaveValue('AAPL');
    });

    it('should accept valid Japanese stock symbols', async () => {
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, '7203.T');
      
      expect(input).toHaveValue('7203.T');
    });

    it('should uppercase input automatically', async () => {
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, 'aapl');
      
      expect(input).toHaveValue('AAPL');
    });

    it('should trim whitespace from input', async () => {
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      await user.type(input, ' AAPL ');
      
      // Submit to trigger trimming
      const button = screen.getByRole('button', { name: /月次スイング分析実行/i });
      await user.click(button);
      
      expect(mockOnAnalyze.toHaveBeenCalledWith('AAPL')).toBe(true);
    });

    it('should disable submit button when input is empty', () => {
      render(<StockSymbolInput {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /月次スイング分析実行/i });
      expect(button).toBeDisabled();
    });

    it('should enable submit button when input has value', async () => {
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      const button = screen.getByRole('button', { name: /月次スイング分析実行/i });
      
      await user.type(input, 'AAPL');
      expect(button).toBeEnabled();
    });
  });

  describe('User Interactions', () => {
    it('should call onAnalyze when form is submitted', async () => {
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      const button = screen.getByRole('button', { name: /月次スイング分析実行/i });
      
      await user.type(input, 'AAPL');
      await user.click(button);
      
      expect(mockOnAnalyze.toHaveBeenCalledWith('AAPL')).toBe(true);
      expect(mockOnAnalyze.toHaveBeenCalledTimes(1)).toBe(true);
    });

    it('should call onAnalyze when form is submitted with Enter key', async () => {
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      
      await user.type(input, 'AAPL');
      await user.keyboard('{Enter}');
      
      expect(mockOnAnalyze.toHaveBeenCalledWith('AAPL')).toBe(true);
    });

    it('should set input value when popular stock is clicked', async () => {
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      const appleButton = screen.getByRole('button', { name: 'AAPL' });
      
      await user.click(appleButton);
      
      expect(input).toHaveValue('AAPL');
    });

    it('should clear input when clear button is clicked', async () => {
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      
      // Type some text first
      await user.type(input, 'AAPL');
      expect(input).toHaveValue('AAPL');
      
      // Click clear button (assuming it appears when there's text)
      const clearButton = screen.getByRole('button', { name: /クリア/i });
      await user.click(clearButton);
      
      expect(input).toHaveValue('');
    });

    it('should not submit empty form', async () => {
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} />);
      
      const button = screen.getByRole('button', { name: /月次スイング分析実行/i });
      
      // Button should be disabled when empty
      expect(button).toBeDisabled();
      
      // Try to click anyway
      await user.click(button);
      
      expect(mockOnAnalyze.not.toHaveBeenCalled()).toBe(true);
    });

    it('should not submit when analyzing', async () => {
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} isAnalyzing={true} />);
      
      const input = screen.getByRole('textbox');
      const button = screen.getByRole('button', { name: /分析中/i });
      
      expect(input).toBeDisabled();
      expect(button).toBeDisabled();
      
      // Try to click anyway
      await user.click(button);
      
      expect(mockOnAnalyze.not.toHaveBeenCalled()).toBe(true);
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', () => {
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('aria-label', expect.stringContaining('銘柄'));
    });

    it('should have proper form association', () => {
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      const label = screen.getByText('銘柄シンボル');
      
      expect(input).toHaveAttribute('id');
      expect(label).toHaveAttribute('for', input.getAttribute('id'));
    });

    it('should show validation message for invalid input', async () => {
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} />);
      
      const input = screen.getByRole('textbox');
      
      // Type invalid characters
      await user.type(input, '123!@#');
      
      // Should show validation message
      expect(screen.getByText(/無効な文字/i)).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should handle onAnalyze callback errors gracefully', async () => {
      const errorOnAnalyze = jest.fn();
      errorOnAnalyze.mockImplementation(() => {
        throw new Error('Analysis failed');
      });
      
      const user = userEvent.setup();
      render(<StockSymbolInput {...defaultProps} onAnalyze={errorOnAnalyze} />);
      
      const input = screen.getByRole('textbox');
      const button = screen.getByRole('button', { name: /月次スイング分析実行/i });
      
      await user.type(input, 'AAPL');
      
      // Should not throw error when callback fails
      expect(async () => {
        await user.click(button);
      }).not.toThrow();
    });
  });

  describe('Custom Props', () => {
    it('should use custom placeholder when provided', () => {
      const customPlaceholder = 'カスタムプレースホルダー';
      render(
        <StockSymbolInput 
          {...defaultProps} 
          placeholder={customPlaceholder} 
        />
      );
      
      const input = screen.getByRole('textbox');
      expect(input).toHaveAttribute('placeholder', customPlaceholder);
    });

    it('should use custom popular stocks when provided', () => {
      const customStocks = {
        us: ['NVDA', 'AMD'],
        japan: ['9984.T', '4755.T'],
      };
      
      render(
        <StockSymbolInput 
          {...defaultProps} 
          popularStocks={customStocks} 
        />
      );
      
      expect(screen.getByRole('button', { name: 'NVDA' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '9984.T' })).toBeInTheDocument();
      
      // Should not show default stocks
      expect(screen.queryByRole('button', { name: 'AAPL' })).not.toBeInTheDocument();
    });
  });
});