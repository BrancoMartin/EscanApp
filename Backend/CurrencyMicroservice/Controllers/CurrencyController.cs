using Application.Interfaces;
using Microsoft.AspNetCore.Mvc;

namespace CurrencyMicroservice.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class CurrencyController : ControllerBase
    {
        private readonly ICurrencyService _currencyService;

        public CurrencyController(ICurrencyService currencyService)
        {
            _currencyService = currencyService;
        }

        [HttpGet("rate/{fromCurrency}/{toCurrency}")]
        public async Task<IActionResult> GetExchangeRate(string fromCurrency, string toCurrency)
        {
            try
            {
                var rate = await _currencyService.GetExchangeRate(fromCurrency.ToUpper(), toCurrency.ToUpper());
                return Ok(new { from = fromCurrency.ToUpper(), to = toCurrency.ToUpper(), rate });
            }
            catch (Exception ex)
            {
                return BadRequest(new { error = ex.Message });
            }
        }

        [HttpGet("convert/{amountInArs}")]
        public async Task<IActionResult> ConvertArsToUsd(decimal amountInArs)
        {
            try
            {
                var result = await _currencyService.ConvertArsToUsd(amountInArs);
                return Ok(new { amount_in_ars = amountInArs, amount_in_usd = result });
            }
            catch (Exception ex)
            {
                return BadRequest(new { error = ex.Message });
            }
        }
    }
}
