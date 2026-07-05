using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using StoreApi.API.Dtos;

namespace StoreApi.API.Controllers;

[ApiController]
[Route("[controller]")]
public class OrderItemController : ControllerBase
{
    [HttpGet]
    public ActionResult<List<OrderItemDto>> GetAll()
    {
        return Ok(new List<OrderItemDto>());
    }

    [HttpGet("{id}")]
    public ActionResult<OrderItemDto> GetById(Guid id)
    {
        return Ok(new OrderItemDto());
    }

    [HttpPost]
    public ActionResult<OrderItemDto> Create(OrderItemDto request)
    {
        return CreatedAtAction(nameof(GetById), new { id = request.ProductId }, request);
    }
}
