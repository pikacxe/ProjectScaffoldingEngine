using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using StoreApi.API.Dtos;
using StoreApi.Domain.Entities;
using StoreApi.Application.Cqrs;
using MediatR;
using Mapster;

namespace StoreApi.API.Controllers;

[ApiController]
[Route("[controller]")]
public class OrderController : ControllerBase
{
    private readonly IMediator _mediator;

    public OrderController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<ActionResult<List<OrderDto>>> GetAll()
    {
        var entities = await _mediator.Send(new GetAllOrderQuery());
        var response = entities.Select(entity => entity.Adapt<OrderDto>()).ToList();
        return Ok(response);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<OrderDto>> GetById(Guid id)
    {
        var entity = await _mediator.Send(new GetOrderByIdQuery(id));
        if (entity is null)
        {
            return NotFound();
        }

        return Ok(entity.Adapt<OrderDto>());
    }

    [HttpPost]
    public async Task<ActionResult<OrderDto>> Create(OrderDto request)
    {
        var entity = request.Adapt<Order>();
        var created = await _mediator.Send(new CreateOrderCommand(entity));
        return CreatedAtAction(nameof(GetById), new { id = created.Id }, created.Adapt<OrderDto>());
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(Guid id, OrderDto request)
    {
        var entity = request.Adapt<Order>();
        var updated = await _mediator.Send(new UpdateOrderCommand(id, entity));
        if (!updated)
        {
            return NotFound();
        }

        return NoContent();
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        var deleted = await _mediator.Send(new DeleteOrderCommand(id));
        if (!deleted)
        {
            return NotFound();
        }

        return NoContent();
    }
}
