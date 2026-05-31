using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;

namespace StoreApi.API.Controllers;

[ApiController]
[Route("[controller]")]
public class OrderController : ControllerBase
{
    [HttpGet]
    public ActionResult<List<OrderDto>> GetAll()
    {
        return Ok(new List<OrderDto>());
    }

    [HttpGet("{id}")]
    public ActionResult<OrderDto> GetById(Guid id)
    {
        return Ok(new OrderDto());
    }

    [HttpPost]
    public ActionResult<OrderDto> Create(OrderDto request)
    {
        return CreatedAtAction(nameof(GetById), new { id = request.Id }, request);
    }
}
