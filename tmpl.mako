


<table border="1">.
<tbody>

% for inst in instances:
	<tr>
		<td>${ inst.node.__class__.__name__ }</td>
		<td><pre>${ inst.print_code() }</pre></td>
		## <td><pre>${ inst.print_code_exact() }</pre></td>
	</tr>
% endfor

</tbody>
</table>