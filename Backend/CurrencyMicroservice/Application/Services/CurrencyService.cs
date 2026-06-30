using Application.Interfaces;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Net.Http;

namespace Application.Services
{
    public class CurrencyService : ICurrencyService
    {
        private readonly IHttpClientFactory _httpClientFactory;

        public CurrencyService(IHttpClientFactory httpClientFactory)
        {
            _httpClientFactory = httpClientFactory;
        }

        public async Task<decimal> ConvertArsToUsd(decimal amountInArs)
        {
            var rate = await GetExchangeRate("ARS", "USD");
            return amountInArs * rate;
        }

        public async Task<decimal> GetExchangeRate(string fromCurrency, string toCurrency)
        {
            var client = _httpClientFactory.CreateClient("ExchangeRateAPI");

            try
            {
                var response = await client.GetAsync($"latest/{fromCurrency}");
                response.EnsureSuccessStatusCode();

                var content = await response.Content.ReadAsStringAsync();
                var exchangeData = JsonSerializer.Deserialize<ExchangeRateResponse>(content);

                if (exchangeData?.rates != null && exchangeData.rates.ContainsKey(toCurrency))
                {
                    return exchangeData.rates[toCurrency];
                }

                throw new Exception($"No se pudo obtener la tasa de cambio para {fromCurrency} a {toCurrency}");
            }
            catch (Exception ex)
            {
                throw new Exception($"Error al consultar el servicio de cambio: {ex.Message}");
            }
        }
    }

    public class ExchangeRateResponse
    {
        public string result { get; set; }
        public string base_code { get; set; }
        public Dictionary<string, decimal> rates { get; set; }
    }
}
