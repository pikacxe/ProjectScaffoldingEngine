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
public class OrderItemController : ControllerBase
{
    private readonly IMediator _mediator;

    public OrderItemController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<ActionResult<List<OrderItemDto>>> GetAll()
    {
        var entities = await _mediator.Send(new GetAllOrderItemQuery());
        var response = entities.Select(entity => entity.Adapt<OrderItemDto>()).ToList();
        return Ok(response);
    }

    [HttpGet("{id}")]
    public async Task<ActionResult<OrderItemDto>> GetById(Guid id)
    {
        var entity = await _mediator.Send(new GetOrderItemByIdQuery(id));
        if (entity is null)
        {
            return NotFound();
        }

        return Ok(entity.Adapt<OrderItemDto>());
    }

    [HttpPost]
    public async Task<ActionResult<OrderItemDto>> Create(OrderItemDto request)
    {
        var entity = request.Adapt<OrderItem>();
        var created = await _mediator.Send(new CreateOrderItemCommand(entity));
        return CreatedAtAction(nameof(GetById), new { id = created.ProductId }, created.Adapt<OrderItemDto>());
    }

    [HttpPut("{id}")]
    public async Task<IActionResult> Update(Guid id, OrderItemDto request)
    {
        var entity = request.Adapt<OrderItem>();
        var updated = await _mediator.Send(new UpdateOrderItemCommand(id, entity));
        if (!updated)
        {
            return NotFound();
        }

        return NoContent();
    }

    [HttpDelete("{id}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        var deleted = await _mediator.Send(new DeleteOrderItemCommand(id));
        if (!deleted)
        {
            return NotFound();
        }

        return NoContent();
    }
}
