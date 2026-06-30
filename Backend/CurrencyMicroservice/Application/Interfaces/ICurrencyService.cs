using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Application.Interfaces
{
    public interface ICurrencyService
    {
        Task<decimal> ConvertArsToUsd(decimal amountInArs);
        Task<decimal> GetExchangeRate(string fromCurrency, string toCurrency);
    }
}
